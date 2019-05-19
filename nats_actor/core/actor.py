import asyncio
import logging
import signal
import time
from contextlib import suppress

import uvloop
from nats.aio.client import Client

from nats_actor.core.utils import get_module
from nats_actor.core.utils import InterruptBumper


WORKER_CONTROL_SIGNAL_START = 'START'
WORKER_CONTROL_SIGNAL_STOP = 'STOP'


def set_logger(conf):
    log_level = getattr(logging, conf.LOG_LEVEL, 'WARNING')
    logging.basicConfig(format=conf.LOG_FORMAT, level=log_level)


def get_callback(nats, task_fn):
    async def execute(msg):
        if nats.is_draining:
            logging.debug('Connection is draining')
            raise Exception('draining')

        logging.info((
            'Received message. '
            f'[subject={msg.subject}][fn={task_fn.__name__}]'
            f'[from={msg.reply}]'
        ))

        try:
            with InterruptBumper(attempts=3):
                now = time.perf_counter()
                data = msg.data.decode()
                ret = task_fn(data)
                elapsed = (time.perf_counter() - now) * 1000

                await nats.publish(msg.reply, ret.encode())

                logging.info((
                    'Task finished. '
                    f'[subject={msg.subject}][fn={task_fn.__name__}]'
                    f'[elapsed={elapsed:.3f}ms]'
                ))

        except KeyboardInterrupt:
            await nats.publish(msg.reply, 'KeyboardInterrupt'.encode())
            raise

    return execute


async def get_connection(conf, loop):
    nats = Client()
    await nats.connect(conf.NATS_URL, loop=loop)

    return nats


def get_stop_handler(loop, queue):
    def stop_worker(*args, **kwargs):
        queue.put_nowait(WORKER_CONTROL_SIGNAL_STOP)

    return stop_worker


def get_worker_handler(queue):
    async def handle_worker_signal(msg):
        worker_message = msg.data.decode()
        logging.debug(f'Got worker signal [signal={worker_message}]')

        await queue.put_nowait(worker_message)

    return handle_worker_signal


def generate_runner(conf, queue):
    async def run_forever(loop):
        nats = await get_connection(conf, loop)

        # Setup worker lifecycle handler
        await nats.subscribe(
            conf.WORKER_NAME, cb=get_worker_handler(queue))

        # Register tasks
        for task_spec in conf.TASKS:
            _, task_fn = get_module(task_spec['task'])
            callback = get_callback(nats, task_fn)

            subscription_id = await nats.subscribe(
                task_spec['subject'], queue=task_spec['queue'], cb=callback)

            logging.debug((
                'Task is registered '
                f'[subscription_id={subscription_id}]'
                f'[subject={task_spec["subject"]}]'
                f'[queue={task_spec["queue"]}]'
                f'[task={task_fn.__name__}]'
            ))

        # wait for stop signal
        signal = WORKER_CONTROL_SIGNAL_START
        while signal != WORKER_CONTROL_SIGNAL_STOP:
            signal = await queue.get()

        # Gracefully unsubscribe the subscription
        logging.debug('Drain subscriptions')
        await nats.flush()
        await nats.drain()
        await nats.close()

        return True

    return run_forever


def stop_eventloop_tasks(loop):
    pending_tasks = asyncio.Task.all_tasks()
    for task in pending_tasks:
        logging.debug((
            f'[task={task.__class__.__name__}:{task.__hash__()}]'
        ))
        with suppress(asyncio.CancelledError):
            loop.run_until_complete(task)
            logging.debug(f'{task.__hash__()} [done={task.done()}]')


def start_worker(conf):
    set_logger(conf)

    logging.debug('Init worker - Setup uvloop')
    if conf.UVLOOP_ENABLED:
        uvloop.install()

    logging.debug('Init worker - Prepare eventloop')
    loop = asyncio.get_event_loop()

    logging.debug('Init worker - Generate worker')
    queue = asyncio.Queue()
    runner = generate_runner(conf, queue)

    logging.debug('Init worker - Set signal handler')
    stop_worker = get_stop_handler(loop, queue)
    signal.signal(signal.SIGTERM, stop_worker)

    try:
        logging.info('Start worker')
        loop.run_until_complete(runner(loop))

    except KeyboardInterrupt:
        logging.debug(f'Stop worker - send stop message to worker')
        stop_worker()

    finally:
        logging.info('Stop worker - cancel pending tasks')
        stop_eventloop_tasks(loop)

        logging.info('Stop worker - close eventloop')
        loop.close()
