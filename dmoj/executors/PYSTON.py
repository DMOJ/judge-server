from typing import List, Tuple

from dmoj.executors.python_executor import PythonExecutor


class Executor(PythonExecutor):
    name = 'PYSTON'
    command = 'pyston'
    test_program = "print(__import__('sys').stdin.read(), end='')"
    _pyston_versions: List[Tuple[int, ...]]

    @classmethod
    def parse_version(cls, command, output):
        try:
            cls._pyston_versions = [tuple(map(int, version.split('.'))) for version in cls.version_regex.findall(output)]
            return cls._pyston_versions[2]
        except Exception:
            return None

    @classmethod
    def get_runtime_versions(cls):
        return tuple(list(super().get_runtime_versions()) + [('implementing python', cls._pyston_versions[0])])
