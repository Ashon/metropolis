import asyncio
import logging
import signal
from contextlib import asynccontextmanager
from contextlib import suppress

import uvloop

from metropolis.core.utils import get_module
from metropolis.core.driver import NatsDriver


# Worker constants
WORKER_CONTROL_SIGNAL_START = 'START'
WORKER_CONTROL_SIGNAL_STOP = 'STOP'

WORKER_TASK_TIMEOUT = 30
WORKER_PENDING_AIOTASK_TIMEOUT = 10

# Default configurations
DEFAULT_LOG_LEVEL = 'WARNING'
DEFAULT_LOG_FORMAT = (
    '[%(asctime)s]'
    '[%(process)d/%(processName)s]'
    '[%(name)s:%(levelname)s]'
    '[%(filename)s:%(lineno)d:%(funcName)s]'
    ' %(message)s'
)


def set_logger(log_level, log_format):
    log_level = getattr(logging, log_level, 'WARNING')
    logging.basicConfig(format=log_format, level=log_level)


class Worker(object):
    conf = None

    # nats driver
    _driver = None

    # worker object's eventloop
    _loop = None

    # aio queue for worker lifecycle control
    _queue = None

    # worker tasks
    _tasks = []

    def __init__(self, conf, loop=None):
        self.conf = conf

        log_level = getattr(self.conf, 'LOG_LEVEL', DEFAULT_LOG_LEVEL)
        log_format = getattr(self.conf, 'LOG_FORMAT', DEFAULT_LOG_FORMAT)
        set_logger(log_level, log_format)

        logging.info('Initialize application')

        logging.debug('Setup driver')
        _, serializer = get_module(conf.SERIALIZER_CLASS)
        self._driver = NatsDriver(
            urls=self.conf.NATS_URL.split(','),
            serializer=serializer)

        logging.debug('Setup uvloop')
        if self.conf.UVLOOP_ENABLED:
            uvloop.install()

        # initialize TASK field
        if not getattr(self.conf, 'TASKS', False):
            setattr(self.conf, 'TASKS', [])

        logging.debug('Prepare eventloop')
        self._loop = loop or asyncio.get_event_loop()

        logging.debug('Generate worker')
        self._queue = asyncio.Queue()

        logging.debug('Set signal handler')
        # stop by message
        self._handle_signal = self.create_signal_handler()
        # stop by interrupt
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

    def stop(self, *args, **kwargs):
        """Send stop signal to worker lifecycle handler queue
        """

        self._queue.put_nowait(WORKER_CONTROL_SIGNAL_STOP)

    def create_signal_handler(self):
        """Return nats message handler function stopping worker.
        """

        async def _handle_signal(msg):
            worker_message = msg.data.decode()
            logging.debug(f'Got worker signal [signal={worker_message}]')

            await self._queue.put_nowait(worker_message)
        return _handle_signal

    @property
    def run_until_complete(self):
        return self._loop.run_until_complete

    @asynccontextmanager
    async def nats_driver(self):
        nats = await self._driver.get_connection(self._loop)

        yield nats

        # Gracefully unsubscribe the subscription
        await self._driver.close()

    def task(self, subject, queue):
        """Register task decorator

        Example:
            @worker.task(subject='foo.get', queue='worker')
            def mytask(data, *args, **kwargs):
                return data[0][::-1]
        """

        def worker_task(task_fn):
            self.conf.TASKS.append({
                'subject': subject,
                'queue': queue,
                'task': task_fn
            })

            return task_fn

        return worker_task

    async def _run_in_loop(self):
        async with self.nats_driver() as nats:

            # Setup worker lifecycle handler
            if self.conf.CONTROL_LIFECYCLE_ENABLED:
                await nats.subscribe(
                    self.conf.WORKER_NAME, cb=self._handle_signal)

            # Register tasks
            for task_spec in self.conf.TASKS:
                if type(task_spec) is str:
                    _, task_fn = get_module(task_spec['task'])
                else:
                    task_fn = task_spec['task']

                # more complicated: self._driver.create_task
                callback = self._driver.create_task_simple(task_fn)

                subscription_id = await nats.subscribe_async(
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
                    self._loop.run_until_complete(
                        asyncio.wait_for(task, WORKER_PENDING_AIOTASK_TIMEOUT))
                    logging.debug(f'{task.__hash__()} [done={task.done()}]')

            logging.info('Stop - close eventloop')
            self._loop.close()

        logging.info('Bye')

    async def async_request(self, name, payload):
        async with self.nats_driver() as nats:
            res = await nats.request(name, payload, timeout=WORKER_TASK_TIMEOUT)
            return res

    async def async_publish(self, name, payload):
        async with self.nats_driver() as nats:
            await nats.publish(name, payload, timeout=WORKER_TASK_TIMEOUT)

    def request(self, name, payload):
        response = self._loop.run_until_complete(
            self.async_request(name, payload))
        return response

    def publish(self, name, payload):
        response = self._loop.run_until_complete(
            self.async_publish(name, payload))
        return response
