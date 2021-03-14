from typing import Tuple

from sanic import Sanic
from sanic.response import json

from metropolis.core.executor import Executor


class Gateway(Executor):
    app = None
    nats = None

    def __init__(self, name, config):
        super(Gateway, self).__init__(name, config)

        self.app = Sanic()
        self.app.listener('before_server_start')(self.setup)
        self.app.listener('after_server_stop')(self.stop)
        self.app.route('/_routes/', methods=['GET'])(self.get_routes)
        self.app.route('/<path:[^/].*?>', methods=['GET'])(self.resolve_message)

    async def setup(self, app, loop):
        """ Bind worker with sanic application eventloop
        """

        self.nats = await self._driver.get_connection(loop)

    async def stop(self, app, loop):
        self.nats = await self._driver.close()

    def serialize_request_to_nats_message(self, request,
                                          path: str) -> Tuple[str, str]:
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

    async def get_routes(self, request):
        # TODO: Returns routemap from nats 'connz?subs=1'
        self.nats
        return json({})

    async def resolve_message(self, request, path: str):
        (route, body) = self.serialize_request_to_nats_message(request, path)

        # data transport
        message = self._driver.serializer.serialize(body)
        worker_response = await self.nats.request(route, message)

        worker_response_dict = self._driver.serializer.deserialize(
            worker_response.data)
        response_data = worker_response_dict['data']

        return json(response_data, status=worker_response_dict['code'])
