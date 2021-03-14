import logging
import time

from nats.aio.client import Client

from metropolis.core.utils import InterruptBumper


WORKER_STATE_CONNECTED = 'connected'
WORKER_STATE_DISCONNECTED = 'connected'
WORKER_STATE_ERROR = 'error'
WORKER_STATE_CLOSED = 'closed'


class NatsDriver(object):
    nats = None
    serializer = None
    state = None

    def __init__(self, urls, serializer):
        self.urls = urls
        self.serializer = serializer

    async def get_connection(self, loop):
        self.nats = Client()

        await self.nats.connect(
            servers=self.urls,
            loop=loop,
            io_loop=loop,
            error_cb=self.get_error_cb(),
            disconnected_cb=self.get_disconnected_cb(),
            closed_cb=self.get_closed_cb(),
            reconnected_cb=self.get_reconnected_cb()
        )

        self.state = WORKER_STATE_CONNECTED

        return self.nats

    def get_error_cb(self):
        async def on_error(exception):
            self.state = WORKER_STATE_ERROR
            logging.error(f'{exception} {self.urls}')

        return on_error

    def get_disconnected_cb(self):
        async def on_disconnected():
            self.state = WORKER_STATE_DISCONNECTED
            logging.info(f'disconnected')

        return on_disconnected

    def get_closed_cb(self):
        async def on_closed():
            self.state = WORKER_STATE_DISCONNECTED
            logging.info(f'closed')

        return on_closed

    def get_reconnected_cb(self):
        async def on_reconnected():
            self.state = WORKER_STATE_CONNECTED
            logging.info(f'reconnected')

        return on_reconnected

    async def execute(self, task_fn, msg):
        """ Execute worker task

        Deserialize data and execute function.
        """

        data = self.serializer.deserialize(msg.data)

        try:
            ret = task_fn(**data)
            code = 200

        except Exception as e:
            ret = str(e)
            code = 500

        if msg.reply:
            response_data = self.serializer.serialize({
                'code': code,
                'data': ret
            })

            await self.nats.publish(msg.reply, response_data)

    async def execute_with_profile(self, task_fn, msg):
        logging.info((
            'Received message. '
            f'[subject={msg.subject}][fn={task_fn.__name__}]'
            f'[from={msg.reply}]'
        ))

        now = time.perf_counter()
        await self.execute(task_fn, msg)
        elapsed = (time.perf_counter() - now) * 1000

        logging.info((
            'Task finished. '
            f'[subject={msg.subject}][fn={task_fn.__name__}]'
            f'[elapsed={elapsed:.3f}ms]'
        ))

    def create_task_simple(self, task_fn):
        logging.debug(f'Create task [task_fn={task_fn.__name__}]')

        async def run_task(msg):
            # more throughputs
            # await self.execute(task_fn, msg)

            # profiles
            await self.execute_with_profile(task_fn, msg)

        return run_task

    def create_task(self, task_fn):
        """ Create durable task

        It considers nats' status and keep task's fails with interrupt bumper.
        """

        logging.debug(f'Create task [task_fn={task_fn.__name__}]')

        async def run_task(msg):
            if self.nats.is_draining:
                logging.debug('Connection is draining')
                raise Exception('draining')

            try:
                with InterruptBumper(attempts=3):
                    # more throughputs
                    # await self.execute(task_fn, msg)

                    # profiles
                    await self.execute_with_profile(task_fn, msg)

            except KeyboardInterrupt:
                await self.nats.publish(
                    msg.reply, 'KeyboardInterrupt'.encode())
                raise

        return run_task

    async def close(self):
        logging.debug('Drain subscriptions')

        await self.nats.flush()
        logging.debug('Flushed')

        await self.nats.drain()
        logging.debug('Drained')

        await self.nats.close()
        logging.debug('Closed')
