import unittest

from dmoj.error import CompileError
from dmoj.executors.JAVA8 import Executor as JAVA8Executor


class ProblemTest(unittest.TestCase):
    def test_malformed_unicode(self):
        source = b"""\
public class malformed {
    public static void main(String[] args){
        S = "\xc1\xbf"; // This is malformed unicode
    }
}"""
        with self.assertRaisesRegex(CompileError, 'Your UTF-8 is bad, and you should feel bad'):
            JAVA8Executor('malformed', source)
