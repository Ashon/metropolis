import unittest

from metropolis.core.serializer import DefaultMessageSerializer
from metropolis.core.serializer import JsonMessageSerializer


class TestDefaultMessageSerializer(unittest.TestCase):
    def test_default_serializer_should_returns_bytes_msg(self):
        msg = 'hello'
        encoded = DefaultMessageSerializer.serialize(msg)
        self.assertEqual(type(encoded), bytes)

    def test_default_serializer_should_returns_string_msg(self):
        byte_msg = b'hello'
        decoded = DefaultMessageSerializer.deserialize(byte_msg)
        self.assertEqual(type(decoded), str)


class TestJsonMessageSerializer(unittest.TestCase):
    def test_default_serializer_should_returns_bytes_msg(self):
        msg = {"msg": "hello"}
        encoded = JsonMessageSerializer.serialize(msg)
        self.assertEqual(type(encoded), bytes)

    def test_default_serializer_should_returns_string_msg(self):
        byte_msg = b'{"msg": "hello"}'
        decoded = JsonMessageSerializer.deserialize(byte_msg)
        self.assertEqual(type(decoded), dict)
