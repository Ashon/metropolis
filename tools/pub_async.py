import os
import sys
sys.path.append(os.getcwd()) # noqa E402

import time

from metropolis.worker import Worker
from example.app import settings


async def publish_msg(worker, name, payload):
    now = time.perf_counter()
    async with worker.nats_driver() as nats:
        for i in range(100000):
            _ = await nats.publish(name, payload)
            if i % 1000 == 0:
                elapsed = time.perf_counter() - now
                print(f'{1000 / elapsed:.3f} RPS ({i} msgs)')
                now = time.perf_counter()


def main(name):
    worker = Worker(__name__, settings)
    payload = b'{"data":"hello"}'

    worker.run_until_complete(
        publish_msg(worker, name, payload)
    )


if __name__ == "__main__":
    main('foo.get')
