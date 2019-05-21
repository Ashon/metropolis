import os

env = os.environ


# eventloop settings
UVLOOP_ENABLED = True

# nats broker settings
NATS_URL = env.get('NATS_URL', 'nats://nats:4222')
QUEUE_NAME = 'tasks'
WORKER_NAME = 'worker'

# worker settings
HEARTBEAT_INTERVAL = 5

# logger settings
LOG_LEVEL = 'ERROR'
LOG_FORMAT = (
    '[%(asctime)s]'
    '[%(process)d/%(processName)s]'
    '[%(name)s:%(levelname)s]'
    '[%(filename)s:%(lineno)d:%(funcName)s]'
    ' %(message)s'
)

# task settings
TASKS = [{
    'subject': 'foo',
    'queue': 'worker',
    'task': 'example.tasks.mytask'
}]
