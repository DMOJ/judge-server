import errno

from .python_executor import PythonExecutor
from dmoj.judgeenv import env


class Executor(PythonExecutor):
    command = env['runtime'].get('pypy')
    test_program = "print __import__('sys').stdin.read()"
    name = 'PYPY'
    fs = ['.*\.(?:so|py[co]?$)', '/proc/cpuinfo$', '/proc/meminfo$', '/etc/localtime$', '/dev/urandom$'] + [command] \
         + ([env['runtime']['pypydir']] if 'pypydir' in env['runtime'] else [])

    def get_security(self, **kwargs):
        security = super(Executor, self).get_security(**kwargs)
        from dmoj.cptbox.syscalls import sys_unlink

        def eaccess(debugger):
            def handle_return():
                debugger.result = -errno.EACCES

            debugger.syscall = debugger.getpid_syscall
            debugger.on_return(handle_return)
            return True

        security[sys_unlink] = eaccess
        return security
