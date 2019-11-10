import os
import signal
import threading
import time
import unittest

from metropolis.core.utils import get_module
from metropolis.core.utils import simple_eventloop
from metropolis.core.utils import InterruptBumper


def simple_fn():
    return 'simple_fn'


async def simple_async_fn():
    return 'async_fn'


class TestUtilsGetModule(unittest.TestCase):
    def test_get_module(self):
        module_name = 'metropolis.core.tests.test_utils.simple_fn'
        module, fn = get_module(module_name)
        self.assertEqual(fn(), 'simple_fn')


class TestUtilsSimpleEventloop(unittest.TestCase):
    def test_async_function_in_simple_eventloop(self):
        msg = ''
        with simple_eventloop() as loop:
            msg = loop.run_until_complete(simple_async_fn())

        self.assertEqual(msg, 'async_fn')


def bumperred_task(bumper, bucket):
    # long running task
    with bumper:
        time.sleep(5)
        bucket['return'] = 1


class TestUtilsInterruptBumper(unittest.TestCase):
    def test_task_should_finished(self):
        pid = os.getpid()
        bumper = InterruptBumper(3)
        bucket = {}

        def stop_signal():
            time.sleep(1)
            os.kill(pid, signal.SIGINT)
        thread = threading.Thread(target=stop_signal)
        thread.daemon = True
        thread.start()

        with self.assertRaises(KeyboardInterrupt):
            bumperred_task(bumper, bucket)

        self.assertEqual(bumper.attempts, 2)
        self.assertEqual(bucket['return'], 1)

    def test_task_should_be_interrupted(self):
        pid = os.getpid()
        bumper = InterruptBumper(3)
        bucket = {}

        def stop_signal():
            for i in range(3):
                time.sleep(1)
                os.kill(pid, signal.SIGINT)
        thread = threading.Thread(target=stop_signal)
        thread.daemon = True
        thread.start()

        with self.assertRaises(KeyboardInterrupt):
            bumperred_task(bumper, bucket)

        self.assertEqual(bumper.attempts, 0)
        self.assertFalse('return' in bucket)
