import unittest

from dmoj.cptbox.filesystem_policies import ExactDir, ExactFile, FilesystemPolicy, RecursiveDir


class CheckerTest(unittest.TestCase):
    def test_exact_dir(self):
        self.fs = FilesystemPolicy([ExactDir('/etc')])

        self.checkTrue('/etc')

        self.checkFalse('/')
        self.checkFalse('/etc/passwd')
        self.checkFalse('/etc/shadow')

    def test_recursive_dir(self):
        self.fs = FilesystemPolicy([RecursiveDir('/usr')])

        self.checkTrue('/usr')
        self.checkTrue('/usr/lib')
        self.checkTrue('/usr/lib/a/b/c/d/e')

        self.checkFalse('/')
        self.checkFalse('/etc')
        self.checkFalse('/us')
        self.checkFalse('/usr2')

    def test_exact_file(self):
        self.fs = FilesystemPolicy([ExactFile('/etc/passwd')])

        self.checkTrue('/etc/passwd')

        self.checkFalse('/')
        self.checkFalse('/etc')
        self.checkFalse('/etc/p')
        self.checkFalse('/etc/passwd2')

    def test_path_checks(self):
        self.fs = FilesystemPolicy([])

        self.assertRaises(AssertionError, self.check, '')
        self.assertRaises(AssertionError, self.check, 'not/an/absolute/path')
        self.assertRaises(AssertionError, self.check, '/usr/lib/not/./a/../normalized/path')

    def test_rule_type_check(self):
        self.assertRaises(AssertionError, ExactFile, '/usr/lib')
        self.assertRaises(AssertionError, ExactDir, '/etc/passwd')
        self.assertRaises(AssertionError, RecursiveDir, '/etc/passwd')

    def test_bad_path_check(self):
        self.assertRaises(AssertionError, ExactFile, 'not/an/absolute/path')
        self.assertRaises(AssertionError, ExactDir, '/nota/./normalized/path')
        self.assertRaises(AssertionError, RecursiveDir, '')

    def check(self, path):
        self.fs.check(path)

    def checkTrue(self, path):
        self.assertTrue(self.fs.check(path))

    def checkFalse(self, path):
        self.assertFalse(self.fs.check(path))
