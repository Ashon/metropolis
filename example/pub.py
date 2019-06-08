import os
import sys
sys.path.append(os.getcwd()) # noqa E402

import random
import time

from nats_worker.core.worker import Worker
from nats_worker.core.utils import simple_eventloop
import settings


def main(name):
    worker = Worker(settings)
    payload = b''

    async def publish_random_msg(worker, loop):
        counter = 0
        now = time.perf_counter()
        async with worker.nats_driver(loop) as nats:
            while 1:
                _ = await nats.request(name, payload)
                counter += 1
                if counter % 100 == 0:
                    elapsed = time.perf_counter() - now
                    print(f'{100 / elapsed:.3f} RPS')
                    now = time.perf_counter()

    with simple_eventloop() as loop:
        loop.run_until_complete(
            publish_random_msg(worker, loop)
        )


if __name__ == "__main__":
    main('foo')
