import os
import unittest

from dmoj.config import InvalidInitException
from dmoj.problem import Problem

try:
    from unittest import mock
except ImportError:
    import mock


class ProblemTest(unittest.TestCase):
    def setUp(self):
        self.data_patch = mock.patch('dmoj.problem.ProblemDataManager')
        data_mock = self.data_patch.start()
        data_mock.side_effect = lambda problem: self.problem_data

    def test_no_init(self):
        self.problem_data = {}
        with self.assertRaises(InvalidInitException):
            Problem('test', 2, 16384)

    def test_empty_init(self):
        self.problem_data = {'init.yml': ''}
        with self.assertRaisesRegexp(InvalidInitException, 'lack of content'):
            Problem('test', 2, 16384)

    def test_bad_init(self):
        self.problem_data = {'init.yml': '"'}
        with self.assertRaisesRegexp(InvalidInitException, 'while scanning a quoted scalar'):
            Problem('test', 2, 16384)

    def test_blank_init(self):
        self.problem_data = {'init.yml': 'archive: does_not_exist.txt'}
        with mock.patch('dmoj.problem.get_problem_root') as gpr:
            gpr.return_value = '/proc'
            with self.assertRaisesRegexp(InvalidInitException, 'archive file'):
                Problem('test', 2, 16384)

    @unittest.skipIf(os.devnull != '/dev/null', 'os.path.exists("nul") is False on Windows')
    def test_bad_archive(self):
        self.problem_data = {'init.yml': 'archive: %s' % (os.devnull,)}
        with mock.patch('dmoj.problem.get_problem_root') as gpr:
            gpr.return_value = '/'
            with self.assertRaisesRegexp(InvalidInitException, 'bad archive:'):
                Problem('test', 2, 16384)

    def tearDown(self):
        self.data_patch.stop()
