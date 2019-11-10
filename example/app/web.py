from sanic import Sanic
from sanic.response import json

from tasks import mytask


app = Sanic()


async def r(request):
    data = request.args.get('data')
    worker_response = mytask(data)

    return json(worker_response)


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

    return (nats_route, request.args)


async def r2(request, path: str):
    (route, body) = serialize_request_to_nats_message(request, path)
    response = mytask(**body)
    return json(response)


# app.route('/foo')(r)
app.route('/<path:[^/].*?>', methods=['GET'])(r2)
app.run(host='0.0.0.0', port='8088')
