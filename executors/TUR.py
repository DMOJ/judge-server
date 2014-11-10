import os
import re
import subprocess

from cptbox import CHROOTSecurity, SecurePopen, PIPE, ALLOW
from cptbox.syscalls import *
from error import CompileError
from .utils import test_executor
from .resource_proxy import ResourceProxy
from judgeenv import env

HASK_FS = ['.*\.so', '.*\.tbc$']


class Executor(ResourceProxy):
    def __init__(self, problem_id, source_code):
        super(Executor, self).__init__()
        source_code_file = self._file('%s.t' % problem_id)
        self.name = self._file(problem_id + ".tbc")
        with open(source_code_file, 'wb') as fo:
            fo.write(source_code)
        ghc_args = [env['runtime']['tprologc'], source_code_file, env['runtime']['turing_dir']]
        ghc_process = subprocess.Popen(ghc_args, stderr=subprocess.PIPE, cwd=self._dir)
        _, compile_error = ghc_process.communicate()
        if ghc_process.returncode != 0:
            raise CompileError(compile_error)
        self.warning = compile_error

    def _get_security(self):
        sec = CHROOTSecurity(HASK_FS)

        sec[sys_getpid] = ALLOW
        sec[sys_getppid] = ALLOW
        sec[sys_clock_getres] = ALLOW
        sec[sys_timer_create] = ALLOW
        sec[sys_timer_settime] = ALLOW
        sec[sys_timer_delete] = ALLOW
        sec[sys_times] = ALLOW
        sec[sys_newselect] = ALLOW # lambda debugger: debugger.arg1() == 0 and debugger.arg2() == 0 and debugger.arg3() == 0

        return sec

    def launch(self, *args, **kwargs):
        return SecurePopen([env['runtime']['tprolog'], self.name] + list(args),
                           security=self._get_security(),
                           time=kwargs.get('time'),
                           memory=kwargs.get('memory'),
                           stderr=(PIPE if kwargs.get('pipe_stderr', False) else None),
                           env={}, cwd=self._dir, nproc=-1)

    def launch_unsafe(self, *args, **kwargs):
        return subprocess.Popen([self.name] + list(args),
                                executable=self.name,
                                env={},
                                cwd=self._dir,
                                **kwargs)


def initialize():
    if 'tprolog' not in env['runtime'] or 'tprologc' not in env['runtime'] or 'turing_dir' not in env['runtime']:
        return False
    return test_executor('TUR', Executor, '''\
put "Hello, World!"
''')
