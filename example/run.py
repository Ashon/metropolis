import os
import sys
sys.path.append(os.getcwd()) # noqa E402

from nats_actor.core.actor import start_worker
import settings

start_worker(settings)
