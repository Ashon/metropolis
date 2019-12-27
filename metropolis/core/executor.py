import logging

from metropolis.core.driver import NatsDriver
from metropolis.core.utils import get_module


# Default configurations
DEFAULT_LOG_LEVEL = 'WARNING'
DEFAULT_LOG_FORMAT = (
    '[%(asctime)s]'
    '[%(process)d/%(processName)s]'
    '[%(name)s:%(levelname)s]'
    '[%(filename)s:%(lineno)d:%(funcName)s]'
    ' %(message)s'
)

DEFAULT_SERIALIZER_CLASS = 'metropolis.core.serializer.DefaultMessageSerializer'
DEFAULT_NATS_URL = 'nats://localhost:4222'
DEFAULT_UVLOOP_ENABLED = True


def set_logger(log_level, log_format):
    log_level = getattr(logging, log_level, 'WARNING')
    logging.basicConfig(format=log_format, level=log_level)


class Executor(object):
    def __init__(self, name, config):
        self.name = name

        self.config = {
            'log_level': getattr(config, 'LOG_LEVEL', DEFAULT_LOG_LEVEL),
            'log_format': getattr(config, 'LOG_FORMAT', DEFAULT_LOG_FORMAT),
            'nats_url': getattr(config, 'NATS_URL', DEFAULT_NATS_URL),
            'serializer_class': getattr(config, 'SERIALIZER_CLASS', DEFAULT_SERIALIZER_CLASS),
            'uvloop_enabled': getattr(config, 'UVLOOP_ENABLED', DEFAULT_UVLOOP_ENABLED),
            'tasks': getattr(config, 'TASKS', []),
            'control_lifecycle': getattr(config, 'CONTROL_LIFECYCLE_ENABLED', False)
        }

        set_logger(self.config['log_level'], self.config['log_format'])
        logging.info('Initialize application')

        logging.debug('Setup serializer')
        _, serializer = get_module(self.config['serializer_class'])

        logging.debug('Setup driver')
        self._driver = NatsDriver(
            urls=self.config['nats_url'].split(','), serializer=serializer)
