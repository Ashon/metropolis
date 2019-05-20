import os
import sys
sys.path.append(os.getcwd()) # noqa E402

import asyncio
import logging
import random
import string

from nats_actor.core.actor import get_connection
import settings


logging.basicConfig(format=settings.LOG_FORMAT, level=logging.INFO)


async def publish(loop, name):
    nats = await get_connection(settings, loop)
    try:
        payload = ''.join(
            random.choice(string.ascii_lowercase)
            for i in range(random.randint(100, 1000))
        ).encode()

        logging.info(f"=> [name={name}][body={payload}]")
        response = await nats.request(name, payload, timeout=10)
        logging.info(f"<= [response={response.data.decode()}]")
    except Exception:
        pass
    # await nats.publish('worker', b'stop')

    await nats.close()


def main(name):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(publish(loop, name))
    loop.close()


if __name__ == "__main__":
    while 1:
        main('foo')
