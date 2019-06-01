import os
import sys
sys.path.append(os.getcwd()) # noqa E402

import random
import string
import time

from nats_worker.core.worker import Worker
import settings


def main(name):
    worker = Worker(settings)
    counter = 0
    now = time.perf_counter()

    while 1:
        payload = ''.join(
            random.choice(string.ascii_lowercase)
            for i in range(random.randint(100, 1000))
        ).encode()

        _ = worker.publish(name, payload)
        counter += 1
        if counter % 100 == 0:
            elapsed = time.perf_counter() - now
            print(f'{100 / elapsed:.3f} RPS')
            now = time.perf_counter()


if __name__ == "__main__":
    main('foo')
