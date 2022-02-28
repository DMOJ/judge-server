import unittest
from io import BytesIO

from dmoj.utils.normalize import normalized_file_copy

TEST_CASE = b'a\r\n\r\r\nb\r\r\nc\nd\n'
TEST_CASE_NO_NEWLINE = b'a\r\n\r\r\nb\r\r\nc\nd'
TEST_CASE_TRAILING_R = b'a\r\n\r\r\nb\r\r\nc\nd\r'
RESULT = b'a\n\n\nb\n\nc\nd\n'


class TestNormalizedCopy(unittest.TestCase):
    def test_simple(self):
        with BytesIO(TEST_CASE) as src, BytesIO() as dst:
            normalized_file_copy(src, dst)
            self.assertEqual(dst.getvalue(), RESULT)

    def test_newline_add(self):
        with BytesIO(TEST_CASE_NO_NEWLINE) as src, BytesIO() as dst:
            normalized_file_copy(src, dst)
            self.assertEqual(dst.getvalue(), RESULT)

    def test_break_after_r(self):
        with BytesIO(TEST_CASE) as src, BytesIO() as dst:
            normalized_file_copy(src, dst, block_size=TEST_CASE.rindex(b'\r\n'))
            self.assertEqual(dst.getvalue(), RESULT)

    def test_break_after_r_newline_add(self):
        with BytesIO(TEST_CASE_NO_NEWLINE) as src, BytesIO() as dst:
            normalized_file_copy(src, dst, block_size=TEST_CASE_NO_NEWLINE.rindex(b'\r\n'))
            self.assertEqual(dst.getvalue(), RESULT)

    def test_break_between_r_n(self):
        with BytesIO(TEST_CASE) as src, BytesIO() as dst:
            normalized_file_copy(src, dst, block_size=TEST_CASE.rindex(b'\r\n') + 1)
            self.assertEqual(dst.getvalue(), RESULT)

    def test_break_between_r_n_newline_add(self):
        with BytesIO(TEST_CASE_NO_NEWLINE) as src, BytesIO() as dst:
            normalized_file_copy(src, dst, block_size=TEST_CASE_NO_NEWLINE.rindex(b'\r\n') + 1)
            self.assertEqual(dst.getvalue(), RESULT)

    def test_break_before_trailing_newline(self):
        with BytesIO(TEST_CASE) as src, BytesIO() as dst:
            normalized_file_copy(src, dst, block_size=len(TEST_CASE) - 1)
            self.assertEqual(dst.getvalue(), RESULT)

    def test_trailing_r(self):
        with BytesIO(TEST_CASE_TRAILING_R) as src, BytesIO() as dst:
            normalized_file_copy(src, dst)
            self.assertEqual(dst.getvalue(), RESULT)

    def test_break_before_trailing_r(self):
        with BytesIO(TEST_CASE_TRAILING_R) as src, BytesIO() as dst:
            normalized_file_copy(src, dst, block_size=len(TEST_CASE_TRAILING_R))
            self.assertEqual(dst.getvalue(), RESULT)
