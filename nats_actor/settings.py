import logging

# eventloop settings
UVLOOP_ENABLED = True

# nats broker settings
NATS_URL = 'localhost:4222'
QUEUE_NAME = 'tasks'
WORKER_NAME = 'worker'

# worker settings
HEARTBEAT_INTERVAL = 5

# logger settings
LOG_LEVEL = logging.DEBUG
LOG_FORMAT = (
    '[%(asctime)s]'
    '[%(process)d/%(processName)s]'
    '[%(name)s:%(levelname)s]'
    '[%(filename)s:%(lineno)d:%(funcName)s]'
    ' %(message)s'
)


def mytask(data):
    return data[::-1]


# task settings
TASKS = [{
    'subject': 'foo',
    'queue': 'worker',
    'task': mytask
}]
