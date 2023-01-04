# type: ignore
import unittest
from pathlib import Path

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
