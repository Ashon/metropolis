import asyncio
import logging
import time
from contextlib import suppress

import uvloop
from nats.aio.client import Client

from nats_actor.core.utils import get_module


WORKER_CONTROL_SIGNAL_START = 'START'
WORKER_CONTROL_SIGNAL_STOP = 'STOP'


def set_logger(conf):
    log_level = getattr(logging, conf.LOG_LEVEL, 'WARNING')
    logging.basicConfig(format=conf.LOG_FORMAT, level=log_level)


def get_callback(nats, task_fn):
    async def execute(msg):
        logging.info((
            'Received message. '
            f'[subject={msg.subject}][fn={task_fn.__name__}]'
            f'[from={msg.reply}]'
        ))

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

        if nats.is_draining:
            logging.debug("Connection is draining")

    return execute


async def get_connection(conf, loop):
    nats = Client()
    await nats.connect(conf.NATS_URL, loop=loop)

    return nats


def get_worker_handler(queue):
    async def handle_worker(msg):
        worker_message = msg.data.decode()
        await queue.put_nowait(worker_message)

    return handle_worker


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

        return True

    return run_forever


def start_worker(conf):
    set_logger(conf)

    logging.debug('Init worker - Setup uvloop')
    if conf.UVLOOP_ENABLED:
        uvloop.install()

    logging.debug('Init worker - Create eventloop')
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    logging.debug('Init worker - Generate worker')
    queue = asyncio.Queue()
    runner = generate_runner(conf, queue)

    try:
        logging.info('Start worker')
        loop.run_until_complete(runner(loop))

    except KeyboardInterrupt:
        logging.debug(f'Stop worker - send stop message to worker')
        queue.put_nowait(WORKER_CONTROL_SIGNAL_STOP)

        logging.info('Stop worker - cancel pending tasks')
        pending_tasks = asyncio.Task.all_tasks()
        for task in pending_tasks:
            logging.debug((
                'Stop worker - cancel '
                f'[task={task.__class__.__name__}:{task.__hash__()}]'
            ))

            with suppress(asyncio.CancelledError):
                loop.run_until_complete(task)

    finally:
        logging.info('Stop worker - close eventloop')
        loop.close()
