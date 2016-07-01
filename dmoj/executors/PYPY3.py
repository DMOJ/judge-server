import os

from .python_executor import PythonExecutor
from dmoj.judgeenv import env


class Executor(PythonExecutor):
    command = env['runtime'].get('pypy3')
    test_program = "print(__import__('sys').stdin.read(), end='')"
    name = 'PYPY3'
    fs = ['.*\.(?:so|py[co]?$)', '/proc/cpuinfo$', '/proc/meminfo$', '/etc/localtime$', '/dev/urandom$'] + [command] \
         + ([env['runtime']['pypy3dir']] if 'pypy3dir' in env['runtime'] else [])

    def get_security(self, **kwargs):
        from dmoj.cptbox.syscalls import sys_mkdir, sys_unlink

        sec = super(Executor, self).get_security(**kwargs)

        def unsafe_pypy3dir(debugger):
            # Relies on the fact this user can't access here.
            return debugger.readstr(debugger.uarg0).startswith(env['runtime']['pypy3dir'])

        if not os.access(env['runtime']['pypy3dir'], os.W_OK):
            sec[sys_mkdir] = unsafe_pypy3dir
            sec[sys_unlink] = unsafe_pypy3dir
        return sec
