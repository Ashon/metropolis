import unittest

from metropolis import Worker


class TestWorker(unittest.TestCase):
    def test_worker_should_be_initialized(self):
        worker = Worker('test-worker')

        self.assertEqual(worker._tasks, [])
        self.assertEqual(worker.config['nats_url'], 'nats://localhost:4222')
        self.assertEqual(
            worker.config['serializer_class'],
            'metropolis.core.serializer.DefaultMessageSerializer')
