import os
import sys
sys.path.append(os.getcwd()) # noqa E402

import asyncio
import logging

from nats_actor.core.actor import get_connection
import settings


logging.basicConfig(format=settings.LOG_FORMAT, level=logging.INFO)


async def publish(loop, name, body):
    nats = await get_connection(settings, loop)
    response = await nats.request(name, body, timeout=10)
    logging.info(f"{response.data.decode()}")
    # await nats.publish('worker', b'stop')

    await nats.close()


def main(name, body):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(publish(loop, name, body))
    loop.close()


if __name__ == "__main__":
    while 1:
        main('foo', b'hello')
