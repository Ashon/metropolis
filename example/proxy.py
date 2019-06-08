import os
import sys
sys.path.append(os.getcwd()) # noqa E402

from sanic import Sanic
from sanic.response import json

from nats_worker.core.worker import Worker
import settings

app = Sanic()


@app.listener('before_server_start')
async def setup(app, loop):
    """ Bind worker with sanic application eventloop
    """

    app.worker = Worker(settings, loop=loop)


def serialize_request_to_nats_message(request, path: str) -> (str, str):
    """Resolve path to nats topic, messages

    Request path convention
    - topic: {path.replace('/', '.'}.{method}.{param['_worker']}
    - message: GET params | POST body

    :Params
        - request: sanic request
        - path <str>: path of url

    :Returns
        <(str, str)>: tuple of topic, message
    """

    nats_route = '.'.join(item for item in (
        path.replace('/', '.'),
        request.method.lower(),
        request.args.get('_worker', '')
    ) if item)

    message = ''

    return (nats_route, message)


@app.route('/<path:[^/].*?>', methods=['GET'])
async def resolve_message(request, path: str):
    (route, body) = serialize_request_to_nats_message(request, path)

    response = await app.worker.async_request('foo', b'hello')
    print(response)

    return json({
        'route': route,
        'body': body,
        'response': response
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
