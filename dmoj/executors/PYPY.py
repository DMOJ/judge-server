from typing import List, Optional, Tuple

from dmoj.executors.base_executor import RuntimeVersionList, VersionTuple
from dmoj.executors.python_executor import PythonExecutor


class Executor(PythonExecutor):
    command = 'pypy'
    pygments_traceback_lexer = 'py2tb'
    test_program = """
import sys
if sys.version_info.major == 2:
    print sys.stdin.read()
"""
    _pypy_versions: List[Tuple[int, ...]]

    @classmethod
    def parse_version(cls, command: str, output: str) -> Optional[VersionTuple]:
        try:
            cls._pypy_versions = [tuple(map(int, version.split('.'))) for version in cls.version_regex.findall(output)]
            return cls._pypy_versions[1]
        except Exception:
            return None

    @classmethod
    def get_runtime_versions(cls) -> RuntimeVersionList:
        # A little hack to report implemented Python version too
        return list(super().get_runtime_versions()) + [('implementing python', cls._pypy_versions[0])]
