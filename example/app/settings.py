import os

env = os.environ


# eventloop settings
UVLOOP_ENABLED = True

# nats broker settings
NATS_URL = env.get('NATS_URL', 'nats://nats:4222')
QUEUE_NAME = 'tasks'
WORKER_NAME = 'worker'
CONTROL_LIFECYCLE_ENABLED = True
SERIALIZER_CLASS = 'nats_worker.core.serializer.JsonMessageSerializer'

# worker settings
HEARTBEAT_INTERVAL = 5

# logger settings
LOG_LEVEL = env.get('LOG_LEVEL', 'ERROR')
LOG_FORMAT = (
    '[%(asctime)s]'
    '[%(process)d/%(processName)s]'
    '[%(name)s:%(levelname)s]'
    '[%(filename)s:%(lineno)d:%(funcName)s]'
    ' %(message)s'
)

# task settings
TASKS = [{
    'subject': 'foo.get',
    'queue': 'worker',
    'task': 'app.tasks.mytask'
}]