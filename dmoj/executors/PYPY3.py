from dmoj.cptbox.handlers import ACCESS_EACCES
from dmoj.executors.PYPY import Executor as PYPYExecutor


class Executor(PYPYExecutor):
    command = 'pypy3'
    test_program = "print(__import__('sys').stdin.read(), end='')"
    name = 'PYPY3'
