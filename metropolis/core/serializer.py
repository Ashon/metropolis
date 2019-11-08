import ujson


class DefaultMessageSerializer(object):
    @staticmethod
    def serialize(msg):
        return msg.encode()

    @staticmethod
    def deserialize(msg):
        return msg.decode()


class JsonMessageSerializer(object):
    @staticmethod
    def serialize(msg):
        return ujson.dumps(msg).encode()

    @staticmethod
    def deserialize(msg):
        return ujson.loads(msg.decode())
