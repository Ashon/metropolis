import os
import sys
sys.path.append(os.getcwd()) # noqa E402

from nats_actor.core.actor import Actor
import settings

actor = Actor(settings)
actor.run()
