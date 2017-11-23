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
