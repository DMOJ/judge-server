from dmoj.executors.PYPY import Executor as PYPYExecutor


class Executor(PYPYExecutor):
    command = 'pypy3'
    test_program = "print(__import__('sys').stdin.read(), end='')"
