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


async def on_error(exception):
    logging.error(f'{exception}')


async def on_disconnected():
    logging.error(f'disconnected')


async def on_closed():
    logging.error(f'closed')


async def on_reconnected():
    logging.error(f'reconnected')


async def get_connection(conf, loop):
    nats = Client()
    await nats.connect(
        servers=[conf.NATS_URL],
        loop=loop,
        error_cb=on_error,
        disconnected_cb=on_disconnected,
        closed_cb=on_closed,
        reconnected_cb=on_reconnected
    )

    return nats


class Actor(object):
    conf = None

    _loop = None
    _queue = None

    def __init__(self, conf):
        self.conf = conf

        set_logger(self.conf)
        logging.info('Init - Initialize application')

        logging.debug('Init - Setup uvloop')
        if self.conf.UVLOOP_ENABLED:
            uvloop.install()

        logging.debug('Init - Prepare eventloop')
        self._loop = asyncio.get_event_loop()

        logging.debug('Init - Generate worker')
        self._queue = asyncio.Queue()

        logging.debug('Init - Set signal handler')
        signal.signal(signal.SIGTERM, self.send_stop_signal)

    def send_stop_signal(self):
        self._queue.put_nowait(WORKER_CONTROL_SIGNAL_STOP)

    async def handle_worker_signal(msg):
        worker_message = msg.data.decode()
        logging.debug(f'Got worker signal [signal={worker_message}]')

        await queue.put_nowait(worker_message)

    async def _run(self):
        nats = await get_connection(self.conf, self._loop)

        # Setup worker lifecycle handler
        await nats.subscribe(
            self.conf.WORKER_NAME, cb=self.handle_worker_signal)

        # Register tasks
        for task_spec in self.conf.TASKS:
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
            signal = await self._queue.get()

        # Gracefully unsubscribe the subscription
        logging.debug('Drain subscriptions')
        await nats.flush()
        await nats.drain()
        await nats.close()

        return True

    def run(self):
        try:
            logging.info('Start - run worker')
            self._loop.run_until_complete(self._run())

        except KeyboardInterrupt:
            logging.debug(f'Stop - send stop message to worker')
            self.send_stop_signal()

        finally:
            logging.info('Stop - cancel pending eventloop tasks')
            pending_tasks = asyncio.Task.all_tasks()
            for task in pending_tasks:
                logging.debug((
                    f'[task={task.__class__.__name__}:{task.__hash__()}]'
                ))
                with suppress(asyncio.CancelledError):
                    self._loop.run_until_complete(task)
                    logging.debug(f'{task.__hash__()} [done={task.done()}]')

            logging.info('Stop - close eventloop')
            self._loop.close()

        logging.info('Bye')
