import unittest


class CheckerTest(unittest.TestCase):
    def test_standard(self):
        from dmoj.checkers.standard import check

        assert check(b'a', b'a')
        assert check(b'a b', b'a  b')
        assert check(b'a b   \n', b'a b')
        assert check(b'\n\na b \n    ', b'a b')
        assert check(b'a\n\n\nb', b'a\nb')
        assert check(b'  a   \n\n', b'\n\n\n  a   \n')
        assert check(b'a ' * 1000, b' a' * 1000)
        assert check(b'a\n' * 1000, b'\n\n\na' * 1000)

        assert not check(b'a', b'b')
        assert not check(b'\n\n\na \n b\n', b'a b')
        assert not check(b'a\n\n\nb', b'a b')

        # Checkers should handle mixed bytes/str
        assert check(b'a', u'a')
        assert not check(b'a', u'b')

    def test_identical(self):
        from dmoj.checkers.identical import check

        def is_pe(res, feedback='Presentation Error, check your whitespace'):
            return res is not True and not res.passed and res.feedback == feedback

        assert check(b'a\nb\nc', b'a\nb\nc')
        assert check(b'a\nb\nc', b'a\nb\nc')
        assert is_pe(check(b'a \nb\nc', b'a\nb\nc'))
        assert is_pe(check(b'a\nb\nc', b'a\nb\nc\n'))
        assert is_pe(check(b'a\nb\nc', b'a\nb\nc\n', pe_allowed=False), feedback=None)

