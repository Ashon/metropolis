import asyncio
import logging
import signal
from contextlib import asynccontextmanager
from contextlib import suppress

import uvloop

from metropolis.core.utils import get_module
from metropolis.core.executor import Executor


# Worker constants
WORKER_CONTROL_SIGNAL_START = '__START__'
WORKER_CONTROL_SIGNAL_STOP = '__STOP__'

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

DEFAULT_SERIALIZER_CLASS = 'metropolis.core.serializer.DefaultMessageSerializer'
DEFAULT_NATS_URL = 'nats://localhost:4222'
DEFAULT_UVLOOP_ENABLED = True


class Worker(Executor):
    config = None

    # worker object's eventloop
    _uvloop_enalbed = None
    _loop = None
    # queue for worker lifecycle control
    _queue = None

    # nats driver
    _driver = None

    # worker tasks
    _tasks = []

    def __init__(self, name, config=None):
        """ Initialize worker

        Build Configuration with args and initialize components

        Bootsteps.
            1. build configuration from constructor args (Executor init phase)
            2. initialize components (Worker init phase)
        """
        super(Worker, self).__init__(name, config)

        logging.debug('Prepare eventloop')
        if self.config['uvloop_enabled']:
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
            self._loop = uvloop.new_event_loop()
        else:
            self._loop = asyncio.get_event_loop()

        # lifecycle controller
        logging.debug('Lifecycle controller')
        self._queue = asyncio.Queue(loop=self._loop)

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
            self.config['tasks'].append({
                'subject': subject,
                'queue': queue,
                'task': task_fn
            })

            return task_fn

        return worker_task

    async def _run_in_loop(self):
        async with self.nats_driver() as nats:
            # Setup worker lifecycle handler
            if self.config['control_lifecycle']:
                await nats.subscribe(
                    self.name, cb=self._handle_signal)

            # Register tasks
            for task_spec in self.config['tasks']:
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
            await nats.publish(name, payload)

    def request(self, name, payload):
        response = self._loop.run_until_complete(
            self.async_request(name, payload))
        return response

    def publish(self, name, payload):
        response = self._loop.run_until_complete(
            self.async_publish(name, payload))
        return response
