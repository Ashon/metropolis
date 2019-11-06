import os
import sys
sys.path.append(os.getcwd()) # noqa E402

import asyncio
import logging

from nats_worker.worker import Worker
from example.app import settings


logging.basicConfig(format=settings.LOG_FORMAT, level=logging.INFO)


async def stop():
    worker = Worker(settings)
    async with worker.nats_driver() as nats:
        await nats.publish(settings.WORKER_NAME, b'STOP')


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(stop())
    loop.close()


if __name__ == "__main__":
    main()
