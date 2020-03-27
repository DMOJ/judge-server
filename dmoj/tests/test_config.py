import unittest

from dmoj.config import ConfigNode


class ConfigNodeTest(unittest.TestCase):
    def setUp(self):
        self.c = ConfigNode(
            defaults={
                'bool': True,
                'int': 1,
                'list': [0, 1, 2],
                'str': 'foo',
                'dict': {'foo': 'bar'},
                'dynamic1+': '5 * 2',
                'dynamic2++': 'node = {"foo": 1, "bar+": "list(range(2))"}',
            }
        )

    def test_primitives(self):
        self.assertIs(self.c.bool, True)
        self.assertEqual(self.c.int, 1)
        self.assertEqual(self.c.str, 'foo')
        self.assertIs(self.c.x, None)

    def test_inheritance(self):
        self.assertIs(self.c.dict.dict.bool, True)

    def test_dict(self):
        self.assertEqual(self.c.dict.foo, 'bar')
        self.assertEqual(list(self.c.dict.keys()), ['foo'])
        self.assertEqual(list(self.c.dict.items()), [('foo', 'bar')])

    def test_list(self):
        self.assertEqual(self.c.list[0], 0)
        self.assertEqual(self.c.list.unwrap(), [0, 1, 2])
        self.assertEqual(len(self.c.list), 3)

        for a, b in enumerate(self.c.list):
            self.assertEqual(a, b)

    def test_simple_dynamic_keys(self):
        self.assertEqual(self.c.dynamic1, 10)

    def test_complex_dynamic_keys(self):
        self.assertEqual(self.c.dynamic2.foo, 1)
        self.assertEqual(self.c.dynamic2.bar.unwrap(), [0, 1])
