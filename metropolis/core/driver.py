import logging
import time

from nats.aio.client import Client

from metropolis.core.utils import InterruptBumper


class NatsDriver(object):
    nats = None
    serializer = None

    def __init__(self, urls, serializer):
        self.urls = urls
        self.serializer = serializer

    async def get_connection(self, loop):
        self.nats = Client()

        await self.nats.connect(
            servers=self.urls,
            loop=loop,
            error_cb=self.on_error,
            disconnected_cb=self.on_disconnected,
            closed_cb=self.on_closed,
            reconnected_cb=self.on_reconnected
        )

        return self.nats

    @staticmethod
    async def on_error(exception):
        logging.error(f'{exception}')

    @staticmethod
    async def on_disconnected():
        logging.info(f'disconnected')

    @staticmethod
    async def on_closed():
        logging.info(f'closed')

    @staticmethod
    async def on_reconnected():
        logging.info(f'reconnected')

    def create_task(self, task_fn):
        logging.debug(f'Create task [task_fn={task_fn.__name__}]')

        async def run_task(msg):
            if self.nats.is_draining:
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

                    elapsed = (time.perf_counter() - now) * 1000

                    logging.info((
                        'Task finished. '
                        f'[subject={msg.subject}][fn={task_fn.__name__}]'
                        f'[elapsed={elapsed:.3f}ms]'
                    ))

            except KeyboardInterrupt:
                await self.nats.publish(
                    msg.reply, 'KeyboardInterrupt'.encode())
                raise

        return run_task

    async def close(self):
        logging.debug('Drain subscriptions')

        await self.nats.flush()
        await self.nats.drain()
        await self.nats.close()
