import os

env = os.environ


# [Worker, Proxy]
# eventloop settings
UVLOOP_ENABLED = True

# nats broker settings
NATS_URL = env.get('NATS_URL', 'nats://nats:4222')
QUEUE_NAME = 'tasks'
WORKER_NAME = 'worker'
CONTROL_LIFECYCLE_ENABLED = True
SERIALIZER_CLASS = 'metropolis.core.serializer.JsonMessageSerializer'

# worker settings
HEARTBEAT_INTERVAL = 5

# logger settings
LOG_LEVEL = env.get('LOG_LEVEL', 'ERROR')
