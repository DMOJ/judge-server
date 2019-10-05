import unittest


class CheckerTest(unittest.TestCase):
    def assert_pass(self, check, str1, str2, expect=True):
        if expect:
            message = 'expecting %r to equal %r'
        else:
            message = 'expecting %r to not equal %r'
        if bool(check(str1, str2)) != expect:
            self.fail(message % (str1, str2))
        if bool(check(str2, str1)) != expect:
            self.fail(message % (str2, str1))

    def assert_fail(self, check, str1, str2):
        self.assert_pass(check, str1, str2, expect=False)

    def test_standard(self):
        from dmoj.checkers.standard import check

        self.assert_pass(check, b'a', b'a')
        self.assert_pass(check, b'a b', b'a  b')
        self.assert_pass(check, b'a b   \n', b'a b')
        self.assert_pass(check, b'\n\na b \n    ', b'a b')
        self.assert_pass(check, b'a\n\n\nb', b'a\nb')
        self.assert_pass(check, b'  a   \n\n', b'\n\n\n  a   \n')
        self.assert_pass(check, b'a ' * 1000, b' a' * 1000)
        self.assert_pass(check, b'a\n' * 1000, b'\n\n\na' * 1000)

        self.assert_fail(check, b'a', b'b')
        self.assert_fail(check, b'\n\n\na \n b\n', b'a b')
        self.assert_fail(check, b'a\n\n\nb', b'a b')
        self.assert_fail(check, b'ab', b'a b')

        # Checkers should handle mixed bytes/str
        self.assert_pass(check, b'a', u'a')
        self.assert_fail(check, b'a', u'b')

    def test_identical(self):
        from dmoj.checkers.identical import check

        def is_pe(res, feedback='Presentation Error, check your whitespace'):
            return res is not True and not res.passed and res.feedback == feedback

        assert check(b'a\nb\nc', b'a\nb\nc')
        assert check(b'a\nb\nc', b'a\nb\nc')
        assert is_pe(check(b'a \nb\nc', b'a\nb\nc'))
        assert is_pe(check(b'a\nb\nc', b'a\nb\nc\n'))
        assert is_pe(check(b'a\nb\nc', b'a\nb\nc\n', pe_allowed=False), feedback=None)

    def test_sorted(self):
        from dmoj.checkers.sorted import check

        assert not check(b'1 2 3', b'3 2 1')
        assert check(b'1 2 3', b'3 2 1', split_on='whitespace')
        assert not check(b'1 2 3', b'3 2 1', split_on='lines')
        assert check(b'1 2 3', b'1 2 3')
        assert not check(b'1 2 2', b'1 2 3')
        assert not check(b'1 2', b'1')
        assert not check(b'1\n2', b'1')
        assert not check(b'12', b'1 2')

        assert check(b'1 2\n3', b'3\n1 2')
        assert not check(b'1 2\n3', b'3\n2 1')
        assert check(b'1 2\n3', b'3\n2 1', split_on='whitespace')
