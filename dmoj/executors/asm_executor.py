import os
import re
import subprocess
from typing import List, Optional

from dmoj.cptbox.tracer import can_debug
from dmoj.error import CompileError
from dmoj.executors.compiled_executor import CompiledExecutor, TimedPopen
from dmoj.judgeenv import env
from dmoj.utils.os_ext import ARCH_X64, ARCH_X86
from dmoj.utils.unicode import utf8text

refeatures = re.compile(r'^[#;@|!]\s*features:\s*([\w\s,]+)', re.M)
feature_split = re.compile(r'[\s,]+').split


class ASMExecutor(CompiledExecutor):
    arch: str
    ld_m: str
    as_name: str
    ld_name: str
    qemu_path: Optional[str] = None
    dynamic_linker: Optional[str] = None
    crt_pre: List[str]
    crt_post: List[str]
    platform_prefixes: Optional[List[str]]

    name = 'ASM'
    ext = 'asm'

    def __init__(self, problem_id, source_code, *args, **kwargs):
        self.use_qemu = self.qemu_path is not None and os.path.isfile(self.qemu_path)
        self.features = self.find_features(source_code)

        super().__init__(problem_id, source_code + b'\n', *args, **kwargs)

    def find_features(self, source_code):
        features = refeatures.search(utf8text(source_code))
        if features is not None:
            return set(filter(None, feature_split(features.group(1))))
        return set()

    @classmethod
    def get_as_path(cls):
        return cls.runtime_dict.get(cls.as_name)

    @classmethod
    def get_ld_path(cls):
        return cls.runtime_dict.get(cls.ld_name)

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
        process = TimedPopen([self.get_ld_path(), '-s', '-o', executable, '-m', self.ld_m] + to_link,
                             cwd=self._dir, stderr=subprocess.PIPE, preexec_fn=self.create_executable_limits(),
                             time_limit=self.compiler_time_limit)
        ld_output = process.communicate()[1]
        if process.returncode != 0:
            raise CompileError(ld_output)

        if as_output or ld_output:
            self.warning = ('%s\n%s' % (utf8text(as_output), utf8text(ld_output))).strip()
        self._executable = executable
        return executable

    def get_cmdline(self):
        if self.use_qemu:
            return [self.qemu_path, self._executable]
        return super().get_cmdline()

    def get_executable(self):
        if self.use_qemu:
            return self.qemu_path
        return super().get_executable()

    def get_fs(self):
        fs = super().get_fs()
        if self.use_qemu:
            fs += ['/proc/sys/vm/mmap_min_addr$', '/etc/qemu-binfmt/', self._executable]
        return fs

    def get_address_grace(self):
        grace = super().get_address_grace()
        if self.use_qemu:
            grace += 65536
        return grace

    @classmethod
    def initialize(cls):
        if cls.qemu_path is None and not can_debug(cls.arch):
            return False
        if any(i is None for i in
               (cls.get_as_path(), cls.get_ld_path(), cls.dynamic_linker, cls.crt_pre, cls.crt_post)):
            return False
        if any(not os.path.isfile(i) for i in (cls.get_as_path(), cls.get_ld_path(), cls.dynamic_linker)):
            return False
        if any(not os.path.isfile(i) for i in cls.crt_pre) or any(not os.path.isfile(i) for i in cls.crt_post):
            return False
        return cls.run_self_test()

    @classmethod
    def get_versionable_commands(cls):
        for runtime in (cls.as_name, cls.ld_name):
            yield runtime, cls.runtime_dict[runtime]

    @classmethod
    def autoconfig(cls):
        if not can_debug(cls.arch):
            return {}, False, 'Unable to natively debug'
        return super().autoconfig()


class GASExecutor(ASMExecutor):
    name = 'GAS'
    as_platform_flag: str

    def get_as_args(self, object):
        as_args = [self.get_as_path(), '-o', object, self._code]
        if os.path.basename(self.get_as_path()) == 'as' and self.as_platform_flag:
            as_args += [self.as_platform_flag]
        return as_args

    def assemble(self):
        object = self._file('%s.o' % self.problem)
        process = subprocess.Popen(self.get_as_args(object),
                                   cwd=self._dir, stderr=subprocess.PIPE)
        as_output = process.communicate()[1]
        if process.returncode != 0:
            raise CompileError(as_output)

        return as_output, [object]

    @classmethod
    def get_find_first_mapping(cls):
        if cls.platform_prefixes is None:
            return None
        return {cls.as_name: ['%s-as' % i for i in cls.platform_prefixes] + ['as'],
                cls.ld_name: ['%s-ld' % i for i in cls.platform_prefixes] + ['ld']}


class NASMExecutor(ASMExecutor):
    name = 'NASM'
    as_name = 'nasm'
    nasm_format: str

    def find_features(self, source_code):
        features = super().find_features(source_code)
        if source_code.startswith(b'; libc'):
            features.add('libc')
        return features

    def get_as_args(self, object):
        return [self.get_as_path(), '-f', self.nasm_format, self._code, '-o', object]

    @classmethod
    def get_version_flags(cls, command):
        return ['-version'] if command == cls.as_name else super().get_version_flags(command)

    @classmethod
    def get_find_first_mapping(cls):
        if cls.platform_prefixes is None:
            return None
        return {cls.ld_name: ['%s-ld' % i for i in cls.platform_prefixes] + ['ld'], 'nasm': ['nasm']}


class PlatformX86Mixin(ASMExecutor):
    arch = ARCH_X86
    ld_name = 'ld_x86'
    ld_m = 'elf_i386'
    platform_prefixes = ['i586-linux-gnu']
    as_platform_flag = '--32'

    qemu_path = env.runtime.qemu_x86
    dynamic_linker = env.runtime['ld.so_x86'] or '/lib/ld-linux.so.2'

    if env.runtime.crt_x86_in_lib32:
        crt_pre = env.runtime.crt_pre_x86 or ['/usr/lib32/crt1.o', '/usr/lib32/crti.o']
        crt_post = env.runtime.crt_post_x86 or ['/usr/lib32/crtn.o']
    else:
        crt_pre = env.runtime.crt_pre_x86 or ['/usr/lib/i386-linux-gnu/crt1.o', '/usr/lib/i386-linux-gnu/crti.o']
        crt_post = env.runtime.crt_post_x86 or ['/usr/lib/i386-linux-gnu/crtn.o']


class PlatformX64Mixin(ASMExecutor):
    arch = ARCH_X64
    ld_name = 'ld_x64'
    ld_m = 'elf_x86_64'
    platform_prefixes = ['x86_64-linux-gnu']
    as_platform_flag = '--64'

    qemu_path = env.runtime.qemu_x64
    dynamic_linker = env.runtime['ld.so_x64'] or '/lib64/ld-linux-x86-64.so.2'
    crt_pre = env.runtime.crt_pre_x64 or ['/usr/lib/x86_64-linux-gnu/crt1.o', '/usr/lib/x86_64-linux-gnu/crti.o']
    crt_post = env.runtime.crt_post_x64 or ['/usr/lib/x86_64-linux-gnu/crtn.o']
