from metropolis import Worker
import settings


worker = Worker(__name__, settings)


@worker.task(subject='foo.get', queue='worker')
def mytask(data, *args, **kwargs):
    """Simple task which returns reverse string
    """

    return data[0][::-1]


worker.run()
