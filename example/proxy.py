import os
import sys
sys.path.append(os.getcwd()) # noqa E402

from nats_worker.proxy import WorkerHttpProxy
import settings


proxy = WorkerHttpProxy(settings)
proxy.app.run(host='0.0.0.0')
