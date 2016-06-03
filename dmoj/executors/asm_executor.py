import os
import re
import subprocess

from dmoj.executors.base_executor import CompiledExecutor
from dmoj.error import CompileError
from dmoj.judgeenv import env

refeatures = re.compile('^[#;@|!]\s*features:\s*([\w\s,]+)', re.M)
feature_split = re.compile('[\s,]+').split


class ASMExecutor(CompiledExecutor):
    as_path = None
    ld_path = None
    qemu_path = None
    dynamic_linker = None
    crt_pre = None
    crt_post = None

    name = 'ASM'
    ext = '.asm'

    def __init__(self, problem_id, source_code, *args, **kwargs):
        self.use_qemu = self.qemu_path is not None and os.path.isfile(self.qemu_path)
        self.features = self.find_features(source_code)

        super(ASMExecutor, self).__init__(problem_id, source_code + '\n', *args, **kwargs)

    def find_features(self, source_code):
        features = refeatures.search(source_code)
        if features is not None:
            return set(filter(None, feature_split(features.group(1))))
        return set()

    def get_as_args(self, object):
        raise NotImplementedError()

    def assemble(self):
        object = self._file('%s.o' % self.problem)
        process = subprocess.Popen(self.get_as_args(object), cwd=self._dir, stderr=subprocess.PIPE)
        as_output = process.communicate()[1]
        if process.returncode != 0:
            raise CompileError(as_output)

        return as_output, [object]

    def compile(self):
        as_output, to_link = self.assemble()

        if 'libc' in self.features:
            to_link = ['-dynamic-linker', self.dynamic_linker] + self.crt_pre + ['-lc'] + to_link + self.crt_post

        executable = self._file(self.problem)
        process = subprocess.Popen([self.ld_path, '-s', '-o', executable] + to_link,
                                   cwd=self._dir, stderr=subprocess.PIPE)
        ld_output = process.communicate()[1]
        if process.returncode != 0:
            raise CompileError(ld_output)

        self.warning = ('%s\n%s' % (as_output, ld_output)).strip()
        return executable

    def get_cmdline(self):
        if self.use_qemu:
            return [self.qemu_path, self._executable]
        return super(ASMExecutor, self).get_cmdline()

    def get_executable(self):
        if self.use_qemu:
            return self.qemu_path
        return super(ASMExecutor, self).get_executable()

    def get_fs(self):
        fs = super(ASMExecutor, self).get_fs()
        if self.use_qemu:
            fs += ['/usr/lib', '/proc', self._executable]
        return fs

    def get_allowed_syscalls(self):
        syscalls = super(ASMExecutor, self).get_allowed_syscalls()
        if self.use_qemu:
            syscalls += ['madvise']
        return syscalls

    def get_address_grace(self):
        grace = super(ASMExecutor, self).get_address_grace()
        if self.use_qemu:
            grace += 65536
        return grace

    @classmethod
    def initialize(cls, sandbox=True):
        if any(i is None for i in (cls.as_path, cls.ld_path, cls.dynamic_linker, cls.crt_pre, cls.crt_post)):
            return False
        if any(not os.path.isfile(i) for i in (cls.as_path, cls.ld_path, cls.dynamic_linker)):
            return False
        if any(not os.path.isfile(i) for i in cls.crt_pre) or any(not os.path.isfile(i) for i in cls.crt_post):
            return False
        return cls.run_self_test(sandbox)


class GASExecutor(ASMExecutor):
    name = 'GAS'

    def get_as_args(self, object):
        return [self.as_path, '-o', object, self._code]

    def assemble(self):
        object = self._file('%s.o' % self.problem)
        process = subprocess.Popen([self.as_path, '-o', object, self._code],
                                   cwd=self._dir, stderr=subprocess.PIPE)
        as_output = process.communicate()[1]
        if process.returncode != 0:
            raise CompileError(as_output)

        return as_output, [object]


class NASMExecutor(ASMExecutor):
    name = 'NASM'
    nasm_format = None

    def find_features(self, source_code):
        features = super(NASMExecutor, self).find_features(source_code)
        if source_code.startswith('; libc'):
            features.add('libc')
        return features

    def get_as_args(self, object):
        return [self.as_path, '-f', self.nasm_format, self._code, '-o', object]


class PlatformX86Mixin(object):
    ld_path = env['runtime'].get('ld_x86', None)
    qemu_path = env['runtime'].get('qemu_x86', None)
    dynamic_linker = env['runtime'].get('ld.so_x86', '/lib/ld-linux.so.2')

    if env['runtime'].get('crt_x86_in_lib32', False):
        crt_pre = env['runtime'].get('crt_pre_x86', ['/usr/lib32/crt1.o', '/usr/lib32/crti.o'])
        crt_post = env['runtime'].get('crt_post_x86', ['/usr/lib32/crtn.o'])
    else:
        crt_pre = env['runtime'].get('crt_pre_x86', ['/usr/lib/i386-linux-gnu/crt1.o', '/usr/lib/i386-linux-gnu/crti.o'])
        crt_post = env['runtime'].get('crt_post_x86', ['/usr/lib/i386-linux-gnu/crtn.o'])


class PlatformX64Mixin(object):
    ld_path = env['runtime'].get('ld_x64', None)
    qemu_path = env['runtime'].get('qemu_x64', None)
    dynamic_linker = env['runtime'].get('ld.so_x64', '/lib64/ld-linux-x86-64.so.2')
    crt_pre = env['runtime'].get('crt_pre_x64',
                                 ['/usr/lib/x86_64-linux-gnu/crt1.o', '/usr/lib/x86_64-linux-gnu/crti.o'])
    crt_post = env['runtime'].get('crt_post_x64', ['/usr/lib/x86_64-linux-gnu/crtn.o'])
