from metropolis import Worker
import settings


worker = Worker('foo', settings)


class Schema(object):
    data: str


@worker.task('get', schema=Schema)
def mytask(request, *args, **kwargs):
    """Simple task which returns reverse string
    """

    return request.data['data'][::-1]


worker.run()
