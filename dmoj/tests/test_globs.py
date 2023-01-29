# type: ignore
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from dmoj import judgeenv
from dmoj.utils.glob_ext import find_glob_root


class TestGlobExt(unittest.TestCase):
    def test_find_glob_root(self):
        self.assertEqual(find_glob_root('/a'), Path('/a'))
        self.assertEqual(find_glob_root('/a/'), Path('/a'))
        self.assertEqual(find_glob_root('/a/b/c'), Path('/a/b/c'))
        self.assertEqual(find_glob_root('/a/*'), Path('/a'))
        self.assertEqual(find_glob_root('/a/*/b'), Path('/a'))
        self.assertEqual(find_glob_root('/a/*/b/*'), Path('/a'))
        self.assertEqual(find_glob_root('/a/**/b/*'), Path('/a'))
        self.assertEqual(find_glob_root('/a/b/**/c/*'), Path('/a/b'))
        self.assertEqual(find_glob_root('/a/b/*'), Path('/a/b'))
        self.assertEqual(find_glob_root('/a/b/c[1-5]'), Path('/a/b'))
        self.assertEqual(find_glob_root('/a/b/c?'), Path('/a/b'))
        self.assertEqual(find_glob_root('/a/b/c?/*'), Path('/a/b'))


class TestConfigGlobs(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.TemporaryDirectory()
        self.root_path = Path(self.root.name)

        dirs = [
            self.root_path / 'ch1' / 'p1',
            self.root_path / 'ch1' / 'p2',
            self.root_path / 'ch2' / 'p3',
            self.root_path / 'ch2' / 'p4',
            self.root_path / 'ch3' / 'ch4' / 'p1',
            self.root_path / 'ch3' / 'ch5' / 'ch6' / 'p5',
            self.root_path / 'ch3' / 'ch5' / 'p6',
        ]
        for dir in dirs:
            dir.mkdir(parents=True)
            (dir / 'init.yml').touch()  # make init.yml

        self.problem_roots = list(
            map(
                str,
                (
                    self.root_path / 'ch1',
                    self.root_path / 'ch2',
                    self.root_path / 'ch3' / 'ch4',
                    self.root_path / 'ch3' / 'ch5',
                    self.root_path / 'ch3' / 'ch5' / 'ch6',
                ),
            )
        )

        self.supported_problems = ['p1', 'p1', 'p4', 'p5', 'p6']

        problem_globs = list(
            map(
                str,
                (
                    self.root_path / 'ch1' / 'p[13]',
                    self.root_path / 'ch2' / 'p[24]',
                    self.root_path / 'ch3' / '**',
                    self.root_path / 'ch7' / '**',
                ),
            )
        )

        self.mock_problem_roots = mock.patch.object(judgeenv, 'problem_globs', problem_globs)

    def test_problem_roots(self):
        with self.mock_problem_roots:
            problem_roots = judgeenv.get_problem_roots()
            self.assertEqual(list(sorted(self.problem_roots)), list(sorted(problem_roots)))

            cases = [
                (self.root_path / 'ch1' / 'p1', 'p1'),
                (self.root_path / 'ch2' / 'p4', 'p4'),
                (self.root_path / 'ch3' / 'ch5' / 'ch6' / 'p5', 'p5'),
                (self.root_path / 'ch3' / 'ch5' / 'p6', 'p6'),
            ]

            for path, problem in cases:
                self.assertEqual(str(path), judgeenv.get_problem_root(problem))

            ex_cases = ['p2', 'p3', 'doesnotexist']

            for problem in ex_cases:
                self.assertRaises(KeyError, judgeenv.get_problem_root, problem)

    def test_supported_problems(self):
        with self.mock_problem_roots:
            supported_problems = judgeenv.get_supported_problems()
            self.assertEqual(list(sorted(self.supported_problems)), list(sorted(supported_problems)))

    def tearDown(self):
        self.root.cleanup()
