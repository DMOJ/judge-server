import unittest

from dmoj.result import CheckerResult


class CheckerTest(unittest.TestCase):
    def assert_standard_pass(self, check, str1, str2, expect=True):
        if expect:
            message = 'expecting %r to equal %r'
        else:
            message = 'expecting %r to not equal %r'
        self.assertEqual(bool(check(str1, str2)), expect, message % (str1, str2))
        self.assertEqual(bool(check(str2, str1)), expect, message % (str2, str1))

    def assert_standard_fail(self, check, str1, str2):
        self.assert_standard_pass(check, str1, str2, expect=False)

    def test_standard(self):
        from dmoj.checkers.standard import check

        self.assert_standard_pass(check, b'a', b'a')
        self.assert_standard_pass(check, b'a b', b'a  b')
        self.assert_standard_pass(check, b'a b   \n', b'a b')
        self.assert_standard_pass(check, b'\n\na b \n    ', b'a b')
        self.assert_standard_pass(check, b'a\n\n\nb', b'a\nb')
        self.assert_standard_pass(check, b'  a   \n\n', b'\n\n\n  a   \n')
        self.assert_standard_pass(check, b'a ' * 1000, b' a' * 1000)
        self.assert_standard_pass(check, b'a\n' * 1000, b'\n\n\na' * 1000)

        self.assert_standard_fail(check, b'a', b'b')
        self.assert_standard_fail(check, b'\n\n\na \n b\n', b'a b')
        self.assert_standard_fail(check, b'a\n\n\nb', b'a b')
        self.assert_standard_fail(check, b'ab', b'a b')

        # Checkers should handle mixed bytes/str
        self.assert_standard_pass(check, b'a', 'a')
        self.assert_standard_fail(check, b'a', 'b')

    def assert_wa_feedback(self, result, feedback):
        self.assertIsInstance(result, CheckerResult)
        self.assertFalse(result.passed)
        self.assertEqual(result.feedback, feedback)

    def assert_identical_pe(self, result):
        self.assert_wa_feedback(result, feedback='Presentation Error, check your whitespace')

    def test_identical(self):
        from dmoj.checkers.identical import check

        self.assertTrue(check(b'a\nb\nc', b'a\nb\nc'))
        self.assertTrue(check(b'a\nb\nc\n', b'a\nb\nc\n'))
        self.assert_identical_pe(check(b'a \nb\nc', b'a\nb\nc'))
        self.assert_identical_pe(check(b'a\nb\nc', b'a\nb\nc\n'))
        self.assert_wa_feedback(check(b'a\nb\nc', b'a\nb\nc\n', pe_allowed=False), feedback=None)

    def test_sorted(self):
        from dmoj.checkers.sorted import check

        self.assertFalse(check(b'1 2 3', b'3 2 1'))
        self.assertTrue(check(b'1 2 3', b'3 2 1', split_on='whitespace'))
        self.assertFalse(check(b'1 2 3', b'3 2 1', split_on='lines'))
        self.assertTrue(check(b'1 2 3', b'1 2 3'))
        self.assertFalse(check(b'1 2 2', b'1 2 3'))
        self.assertFalse(check(b'1 2', b'1'))
        self.assertFalse(check(b'1\n2', b'1'))
        self.assertFalse(check(b'12', b'1 2'))

        self.assertTrue(check(b'1 2\n3', b'3\n1 2'))
        self.assertFalse(check(b'1 2\n3', b'3\n2 1'))
        self.assertTrue(check(b'1 2\n3', b'3\n2 1', split_on='whitespace'))

    def assert_partial(self, result, expected_points, passed):
        self.assertIsInstance(result, CheckerResult)
        self.assertEqual(result.points, expected_points)
        self.assertEqual(result.passed, passed)

    def test_linematches(self):
        from dmoj.checkers.linematches import check

        self.assertFalse(check(b'1', b'1\n2', point_distribution=[1, 1]))
        self.assertFalse(check(b'1\n2', b'1'))

        self.assert_partial(
            check(b'1', b'1\n2', filler_lines_required=False, point_distribution=[4, 6]),
            expected_points=0.4,
            passed=True,
        )
        self.assert_partial(check(b'1\n3', b'1\n2', point_distribution=[4, 6]), expected_points=0.4, passed=True)

        self.assert_partial(check(b'3\n2', b'1\n2', point_distribution=[4, 6]), expected_points=0.6, passed=True)
        self.assert_partial(check(b'1\n2', b'1\n2', point_distribution=[4, 6]), expected_points=1, passed=True)

        self.assert_partial(check(b'1', b'2', point_distribution=[1]), expected_points=0, passed=False)
