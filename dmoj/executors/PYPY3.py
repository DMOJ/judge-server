from dmoj.executors.PYPY import Executor as PYPYExecutor


class Executor(PYPYExecutor):
    command = 'pypy3'
    test_program = """
import sys
if sys.version_info.major == 3:
    print(sys.stdin.read(), end='')
"""
