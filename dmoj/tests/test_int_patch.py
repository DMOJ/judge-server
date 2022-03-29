# type: ignore
import unittest

from parameterized import parameterized_class

from dmoj.utils import builtin_int_patch

int_ = int


@parameterized_class([{'use_patch': True}, {'use_patch': False}])
class IntrospectionTest(unittest.TestCase):
    def setUp(self) -> None:
        if self.use_patch:
            builtin_int_patch.apply()

    def tearDown(self) -> None:
        if self.use_patch:
            builtin_int_patch.unapply()

    def test_instance_check(self):
        self.assertTrue(isinstance(1, int))
        self.assertTrue(isinstance(True, int))
        self.assertFalse(isinstance('', int))
        self.assertFalse(isinstance([], int))
        self.assertFalse(isinstance({}, int))

    def test_subclass_check(self):
        self.assertTrue(issubclass(bool, int))
        self.assertTrue(issubclass(int, int))
        self.assertFalse(issubclass(str, int))
        self.assertFalse(issubclass(list, int))
        self.assertFalse(issubclass(dict, int))

    def test_type_check(self):
        self.assertEqual(type(1), int)

    def test_identity(self):
        self.assertIs(int(), 0)
        self.assertIs(int(1), 1)
        self.assertIs(type(int(1)), int_)


class ParseTest(unittest.TestCase):
    def setUp(self) -> None:
        builtin_int_patch.apply()

    def tearDown(self) -> None:
        builtin_int_patch.unapply()

    def test_parse_string_short(self):
        self.assertEqual(int('1'), 1)
        self.assertEqual(int('-1'), -1)
        self.assertEqual(int('1337'), 1337)
        self.assertEqual(
            int('9' * builtin_int_patch.INT_MAX_NUMBER_DIGITS), 10**builtin_int_patch.INT_MAX_NUMBER_DIGITS - 1
        )

    def test_parse_string_long(self):
        with self.assertRaises(ValueError):
            int('1' + '0' * builtin_int_patch.INT_MAX_NUMBER_DIGITS)

    def test_parse_int(self):
        self.assertEqual(int(1), 1)
        self.assertEqual(int(-1337), -1337)
        self.assertEqual(
            int(10**builtin_int_patch.INT_MAX_NUMBER_DIGITS), 10**builtin_int_patch.INT_MAX_NUMBER_DIGITS
        )
