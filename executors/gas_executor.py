import os
import subprocess

from .base_executor import CompiledExecutor
from error import CompileError
from judgeenv import env

ASM_FS = ['.*\.so']#, '/proc/meminfo', '/dev/null']


class GASExecutor(CompiledExecutor):
    as_path = None
    ld_path = None
    qemu_path = None
    name = 'GAS'
    ext = '.asm'

    def __init__(self, *args, **kwargs):
        self.use_qemu = self.qemu_path is not None and os.path.isfile(self.qemu_path)
        super(GASExecutor, self).__init__(*args, **kwargs)

    def compile(self):
        object = self._file('%s.o' % self.problem)
        process = subprocess.Popen([self.as_path, '-o', object, self._code],
                                   cwd=self._dir, stderr=subprocess.PIPE)
        as_output = process.communicate()[1]
        if process.returncode != 0:
            raise CompileError(as_output)

        executable = self._file(self.problem)
        process = subprocess.Popen([self.ld_path, '-s', '-o', executable, object],
                                   cwd=self._dir, stderr=subprocess.PIPE)
        ld_output = process.communicate()[1]
        if process.returncode != 0:
            raise CompileError(ld_output)

        self.warning = '%s\n%s' % (as_output, ld_output)
        return executable

    def get_cmdline(self):
        if self.use_qemu:
            return [self.qemu_path, self._executable]
        return super(GASExecutor, self).get_cmdline()

    def get_executable(self):
        if self.use_qemu:
            return self.qemu_path
        return super(GASExecutor, self).get_executable()

    def get_fs(self):
        fs = super(GASExecutor, self).get_fs()
        if self.use_qemu:
            fs += ['/usr/lib', '/proc', self._executable]
        return fs

    def get_allowed_syscalls(self):
        syscalls = super(GASExecutor, self).get_allowed_syscalls()
        if self.use_qemu:
            syscalls += ['madvise']
        return syscalls

    def get_address_grace(self):
        grace = super(GASExecutor, self).get_address_grace()
        if self.use_qemu:
            grace += 65536
        return grace

    @classmethod
    def initialize(cls, sandbox=True):
        if cls.as_path is None or cls.ld_path is None:
            return False
        if not os.path.isfile(cls.as_path) or not os.path.isfile(cls.ld_path):
            return False
        return cls.run_self_test(sandbox)
