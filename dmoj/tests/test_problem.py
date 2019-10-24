import os
import unittest
from unittest import mock

from dmoj.config import InvalidInitException
from dmoj.problem import Problem, ProblemDataManager


class ProblemTest(unittest.TestCase):
    def setUp(self):
        self.data_patch = mock.patch('dmoj.problem.ProblemDataManager')
        data_mock = self.data_patch.start()
        data_mock.side_effect = lambda problem: self.problem_data

    def test_test_case_matching(self):
        class MockProblem(Problem):
            def _resolve_archive_files(self):
                return None

            def _problem_file_list(self):
                return [
                    's2.1-1.in', 's2.1-1.out',
                    's2.1.2.in', 's2.1.2.out',
                    's3.4.in', 's3.4.out',
                    '5.in', '5.OUT',
                    '6-1.in', '6-1.OUT',
                    '6.2.in', '6.2.OUT',
                    'foo/a.b.c.6.3.in', 'foo/a.b.c.6.3.OUT',
                    'bar.in.7', 'bar.out.7',
                    'INPUT8.txt', 'OUTPUT8.txt',
                    '.DS_Store',
                ]

        self.problem_data = ProblemDataManager('foo')
        self.problem_data.update({'init.yml': 'archive: foo.zip'})
        self.assertEqual(MockProblem('test', 2, 16384).config.test_cases.unwrap(),
                         [{'batched': [{'in': 's2.1-1.in', 'out': 's2.1-1.out'},
                                       {'in': 's2.1.2.in', 'out': 's2.1.2.out'}], 'points': 1},
                          {'in': 's3.4.in', 'out': 's3.4.out', 'points': 1},
                          {'in': '5.in', 'out': '5.OUT', 'points': 1}, {
                              'batched': [{'in': '6-1.in', 'out': '6-1.OUT'}, {'in': '6.2.in', 'out': '6.2.OUT'},
                                          {'in': 'foo/a.b.c.6.3.in', 'out': 'foo/a.b.c.6.3.OUT'}], 'points': 1},
                          {'in': 'bar.in.7', 'out': 'bar.out.7', 'points': 1},
                          {'in': 'INPUT8.txt', 'out': 'OUTPUT8.txt', 'points': 1}])

    def test_no_init(self):
        self.problem_data = {}
        with self.assertRaises(InvalidInitException):
            Problem('test', 2, 16384)

    def test_empty_init(self):
        self.problem_data = {'init.yml': ''}
        with self.assertRaisesRegex(InvalidInitException, 'lack of content'):
            Problem('test', 2, 16384)

    def test_bad_init(self):
        self.problem_data = {'init.yml': '"'}
        with self.assertRaisesRegex(InvalidInitException, 'while scanning a quoted scalar'):
            Problem('test', 2, 16384)

    def test_blank_init(self):
        self.problem_data = {'init.yml': 'archive: does_not_exist.txt'}
        with mock.patch('dmoj.problem.get_problem_root') as gpr:
            gpr.return_value = '/proc'
            with self.assertRaisesRegex(InvalidInitException, 'archive file'):
                Problem('test', 2, 16384)

    @unittest.skipIf(os.devnull != '/dev/null', 'os.path.exists("nul") is False on Windows')
    def test_bad_archive(self):
        self.problem_data = {'init.yml': 'archive: %s' % (os.devnull,)}
        with mock.patch('dmoj.problem.get_problem_root') as gpr:
            gpr.return_value = '/'
            with self.assertRaisesRegex(InvalidInitException, 'bad archive:'):
                Problem('test', 2, 16384)

    def tearDown(self):
        self.data_patch.stop()
