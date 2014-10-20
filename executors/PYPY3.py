from .PYPY import Executor as PYPYExecutor, PYTHON_FS
from executors.utils import test_executor
from judgeenv import env


class Executor(PYPYExecutor):
    def _executable(self):
        return env['runtime']['pypy3']
    
    def _get_fs(self):
        return PYTHON_FS + ([env['runtime']['pypy3dir']] if 'pypy3dir' in env['runtime'] else [])


def initialize():
    if not 'pypy3' in env['runtime']:
        return False
    return test_executor('PYPY3', Executor, 'print("Hello, World!")')

