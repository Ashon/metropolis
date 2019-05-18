import os
import sys
sys.path.append(os.getcwd()) # noqa E402

import asyncio
import logging

from nats_actor.core.actor import get_connection
import settings


logging.basicConfig(format=settings.LOG_FORMAT, level=logging.INFO)


async def stop(loop):
    nats = await get_connection(settings, loop)
    await nats.publish(settings.WORKER_NAME, b'STOP')

    await nats.close()


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(stop(loop))
    loop.close()


if __name__ == "__main__":
    main()
