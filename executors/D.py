import os
import re
import subprocess

from cptbox import CHROOTSecurity, SecurePopen, PIPE, ALLOW
from cptbox.syscalls import *
from error import CompileError
from .utils import test_executor
from .resource_proxy import ResourceProxy
from judgeenv import env

D_FS = ['.*\.so', '/proc/self/maps$']


class Executor(ResourceProxy):
    def __init__(self, problem_id, source_code):
        super(Executor, self).__init__()
        source_code_file = self._file('%s.d' % problem_id)
        self.name = self._file(problem_id)
        with open(source_code_file, 'wb') as fo:
            fo.write(source_code)
        dmd_args = [env['runtime']['dmd'], '-O', '-inline', '-release', '-w', source_code_file, '-of%s' % problem_id]
        dmd_process = subprocess.Popen(dmd_args, stderr=subprocess.PIPE, cwd=self._dir)
        _, compile_error = dmd_process.communicate()
        if dmd_process.returncode != 0:
            raise CompileError(compile_error)
        self.warning = compile_error

    def _get_security(self):
        sec = CHROOTSecurity(D_FS)
        sec[sys_sched_getaffinity] = ALLOW
        sec[sys_sched_getparam] = ALLOW
        sec[sys_sched_getscheduler] = ALLOW
        sec[sys_sched_get_priority_min] = ALLOW
        sec[sys_sched_get_priority_max] = ALLOW
        sec[sys_clock_getres] = ALLOW
        return sec

    def launch(self, *args, **kwargs):
        return SecurePopen([self.name] + list(args),
                           security=self._get_security(),
                           address_grace=32768,
                           time=kwargs.get('time'),
                           memory=kwargs.get('memory'),
                           stderr=(PIPE if kwargs.get('pipe_stderr', False) else None),
                           env={}, cwd=self._dir)

    def launch_unsafe(self, *args, **kwargs):
        return subprocess.Popen([self.name] + list(args),
                                executable=self.name,
                                env={}, cwd=self._dir,
                                **kwargs)


def initialize():
    if 'dmd' not in env['runtime']:
        return False
    if not os.path.isfile(env['runtime']['dmd']):
        return False
    return test_executor('D', Executor, '''\
import std.stdio;

void main() {
    writeln("Hello, World!");
}
''', problem='self_test')
