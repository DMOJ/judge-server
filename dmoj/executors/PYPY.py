from typing import List, Tuple

from dmoj.executors.python_executor import PythonExecutor


class Executor(PythonExecutor):
    command = 'pypy'
    test_program = """
import sys
if sys.version_info.major == 2:
    print sys.stdin.read()
"""
    _pypy_versions: List[Tuple[int, ...]]

    @classmethod
    def parse_version(cls, command, output):
        try:
            cls._pypy_versions = [tuple(map(int, version.split('.'))) for version in cls.version_regex.findall(output)]
            return cls._pypy_versions[1]
        except Exception:
            return None

    @classmethod
    def get_runtime_versions(cls):
        # A little hack to report implemented Python version too
        return tuple(list(super().get_runtime_versions()) + [('implementing python', cls._pypy_versions[0])])
