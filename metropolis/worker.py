import asyncio
import logging
import signal
from contextlib import asynccontextmanager
from contextlib import suppress

import uvloop

from metropolis.core.utils import get_module
from metropolis.core.utils import simple_eventloop
from metropolis.core.driver import NatsDriver


WORKER_CONTROL_SIGNAL_START = 'START'
WORKER_CONTROL_SIGNAL_STOP = 'STOP'


def set_logger(conf):
    log_level = getattr(logging, conf.LOG_LEVEL, 'WARNING')
    logging.basicConfig(format=conf.LOG_FORMAT, level=log_level)


class Worker(object):
    conf = None

    # nats driver
    _driver = None

    # worker object's eventloop
    _loop = None

    # aio queue for worker lifecycle control
    _queue = None

    def __init__(self, conf, loop=None):
        self.conf = conf

        set_logger(self.conf)
        logging.info('Initialize application')

        logging.debug('Setup driver')
        _, serializer = get_module(conf.SERIALIZER_CLASS)
        self._driver = NatsDriver(
            urls=self.conf.NATS_URL.split(','),
            serializer=serializer)

        logging.debug('Setup uvloop')
        if self.conf.UVLOOP_ENABLED:
            uvloop.install()

        logging.debug('Prepare eventloop')
        self._loop = loop or asyncio.get_event_loop()

        logging.debug('Generate worker')
        self._queue = asyncio.Queue()

        logging.debug('Set signal handler')
        self._handle_signal = self.create_signal_handler()
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

    def stop(self, *args, **kwargs):
        self._queue.put_nowait(WORKER_CONTROL_SIGNAL_STOP)

    def create_signal_handler(self):
        async def _handle_signal(msg):
            worker_message = msg.data.decode()
            logging.debug(f'Got worker signal [signal={worker_message}]')

            await self._queue.put_nowait(worker_message)
        return _handle_signal

    @property
    def run_until_complete(self):
        return self._loop.run_until_complete

    @asynccontextmanager
    async def nats_driver(self, loop=None):
        # remove condition for performance
        loop = loop or self._loop
        nats = await self._driver.get_connection(loop)

        yield nats

        # Gracefully unsubscribe the subscription
        await self._driver.close()

    async def _run_in_loop(self):
        async with self.nats_driver() as nats:

            # Setup worker lifecycle handler
            if self.conf.CONTROL_LIFECYCLE_ENABLED:
                await nats.subscribe(self.conf.WORKER_NAME, cb=self._handle_signal)

            # Register tasks
            for task_spec in self.conf.TASKS:
                _, task_fn = get_module(task_spec['task'])
                callback = self._driver.create_task(task_fn)

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

    def run(self):
        try:
            logging.info('Start - run worker')
            self._loop.run_until_complete(self._run_in_loop())

        except KeyboardInterrupt:
            logging.debug(f'Stop - send stop message to worker')
            self.stop()

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

    async def async_request(self, name, payload, loop=None):
        async with self.nats_driver(loop) as nats:
            res = await nats.request(name, payload)
            return res

    async def async_publish(self, name, payload, loop=None):
        async with self.nats_driver(loop) as nats:
            await nats.publish(name, payload)

    def request(self, name, payload):
        with simple_eventloop() as loop:
            response = loop.run_until_complete(
                self.async_request(name, payload, loop))
            return response

    def publish(self, name, payload):
        with simple_eventloop() as loop:
            response = loop.run_until_complete(
                self.async_publish(name, payload, loop))
            return response
