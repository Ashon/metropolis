import asyncio
import logging
import importlib
import signal
from contextlib import contextmanager


def get_module(module_path):
    module_path, _, child_name = module_path.rpartition('.')

    module = importlib.import_module(module_path)
    child = getattr(module, child_name)

    return module, child


class InterruptBumper(object):
    def __init__(self, attempts):
        self.attempts = attempts

    def __enter__(self):
        self.signal_received = ()
        self.old_handler = signal.signal(signal.SIGINT, self.handler)

    def handler(self, sig, frame):
        self.signal_received = (sig, frame)

        self.attempts -= 1
        logging.warn(f'Bumping interrupts. [remains={self.attempts}]')

        if not self.attempts:
            logging.warn('max attempts reached stop.')
            self.old_handler(*self.signal_received)

    def __exit__(self, type, value, traceback):
        signal.signal(signal.SIGINT, self.old_handler)
        if self.signal_received:
            self.old_handler(*self.signal_received)


@contextmanager
def simple_eventloop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    yield loop

    loop.close()
