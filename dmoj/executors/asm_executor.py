import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from dmoj.cptbox import NATIVE_ABI, PTBOX_ABI_ARM, PTBOX_ABI_ARM64, PTBOX_ABI_X64, PTBOX_ABI_X86, can_debug
from dmoj.cptbox.filesystem_policies import ExactFile, FilesystemAccessRule, RecursiveDir
from dmoj.executors.compiled_executor import CompiledExecutor
from dmoj.judgeenv import env, skip_self_test
from dmoj.utils.unicode import utf8bytes, utf8text

refeatures = re.compile(r'^[#;@|!]\s*features:\s*([\w\s,]+)', re.M)
feature_split = re.compile(r'[\s,]+').split


class ASMExecutor(CompiledExecutor):
    abi: int
    ld_m: str
    as_name: str
    ld_name: str
    qemu_path: Optional[str] = None
    dynamic_linker: str
    crt_pre: List[str]
    crt_post: List[str]
    platform_prefixes: Optional[List[str]]

    ext = 'asm'

    def __init__(self, problem_id: str, source_code: bytes, *args, **kwargs) -> None:
        self.use_qemu = self.qemu_path is not None and os.path.isfile(self.qemu_path)
        self.features = self.find_features(source_code)

        super().__init__(problem_id, source_code + b'\n', *args, **kwargs)

    def find_features(self, source_code: bytes) -> Set[str]:
        features = refeatures.search(utf8text(source_code))
        if features is not None:
            return set(filter(None, feature_split(features.group(1))))
        return set()

    @classmethod
    def get_as_path(cls) -> str:
        return cls.runtime_dict.get(cls.as_name)

    @classmethod
    def get_ld_path(cls) -> str:
        return cls.runtime_dict.get(cls.ld_name)

    def get_as_args(self, obj_file: str) -> List[str]:
        raise NotImplementedError()

    def assemble(self) -> Tuple[bytes, List[str]]:
        obj_file = self._file(f'{self.problem}.o')
        process = self.create_compile_process(self.get_as_args(obj_file))
        as_output = self.get_compile_output(process)
        return as_output, [obj_file]

    def compile(self) -> str:
        as_output, to_link = self.assemble()

        if 'libc' in self.features:
            to_link = ['-dynamic-linker', self.dynamic_linker] + self.crt_pre + ['-lc'] + to_link + self.crt_post

        executable = self._file(self.problem)
        process = self.create_compile_process([self.get_ld_path(), '-s', '-o', executable, '-m', self.ld_m] + to_link)
        ld_output = self.get_compile_output(process)

        if as_output or ld_output:
            self.warning = utf8bytes(f'{utf8text(as_output)}\n{utf8text(ld_output)}').strip()
        self._executable = executable
        return executable

    def get_cmdline(self, **kwargs) -> List[str]:
        if self.use_qemu:
            assert self.qemu_path is not None
            assert self._executable is not None
            return [self.qemu_path, self._executable]
        return super().get_cmdline()

    def get_executable(self) -> str:
        if self.use_qemu:
            assert self.qemu_path is not None
            return self.qemu_path
        return super().get_executable()

    def get_fs(self) -> List[FilesystemAccessRule]:
        fs = super().get_fs()
        if self.use_qemu:
            assert self._executable is not None
            fs += [
                ExactFile('/proc/sys/vm/mmap_min_addr'),
                RecursiveDir('/etc/qemu-binfmt'),
                ExactFile(self._executable),
            ]
        return fs

    def get_address_grace(self) -> int:
        grace = super().get_address_grace()
        if self.use_qemu:
            grace += 65536
        return grace

    @classmethod
    def initialize(cls) -> bool:
        if cls.qemu_path is None and not can_debug(cls.abi):
            return False
        if any(
            i is None for i in (cls.get_as_path(), cls.get_ld_path(), cls.dynamic_linker, cls.crt_pre, cls.crt_post)
        ):
            return False
        if any(not i or not os.path.isfile(i) for i in (cls.get_as_path(), cls.get_ld_path(), cls.dynamic_linker)):
            return False
        if any(not os.path.isfile(i) for i in cls.crt_pre) or any(not os.path.isfile(i) for i in cls.crt_post):
            return False
        # TODO(kirito): this code is also copied in java_executor.py, but judge should be refactored to call
        # `run_self_test` outside of `initialize`.
        return skip_self_test or cls.run_self_test()

    @classmethod
    def get_versionable_commands(cls) -> List[Tuple[str, str]]:
        return [(runtime, cls.runtime_dict[runtime]) for runtime in (cls.as_name, cls.ld_name)]

    @classmethod
    def autoconfig(cls) -> Tuple[Optional[Dict[str, Any]], bool, str, str]:
        if not can_debug(cls.abi):
            return {}, False, 'Unable to natively debug', ''
        return super().autoconfig()


class GASExecutor(ASMExecutor):
    as_platform_flag: str

    def get_as_args(self, obj_file: str) -> List[str]:
        assert self._code is not None
        as_args = [self.get_as_path(), '-o', obj_file, self._code]
        if os.path.basename(self.get_as_path()) == 'as' and getattr(self, 'as_platform_flag', None):
            as_args += [self.as_platform_flag]
        return as_args

    @classmethod
    def get_find_first_mapping(cls) -> Optional[Dict[str, List[str]]]:
        if cls.platform_prefixes is None:
            return None
        return {
            cls.as_name: [f'{i}-as' for i in cls.platform_prefixes] + ['as'],
            cls.ld_name: [f'{i}-ld' for i in cls.platform_prefixes] + ['ld'],
        }


class NASMExecutor(ASMExecutor):
    as_name = 'nasm'
    nasm_format: str

    def find_features(self, source_code: bytes) -> Set[str]:
        features = super().find_features(source_code)
        if source_code.startswith(b'; libc'):
            features.add('libc')
        return features

    def get_as_args(self, obj_file: str) -> List[str]:
        assert self._code is not None
        return [self.get_as_path(), '-f', self.nasm_format, self._code, '-o', obj_file]

    @classmethod
    def get_version_flags(cls, command: str) -> List[str]:
        return ['-version'] if command == cls.as_name else super().get_version_flags(command)

    @classmethod
    def get_find_first_mapping(cls) -> Optional[Dict[str, List[str]]]:
        if cls.platform_prefixes is None:
            return None
        return {cls.ld_name: [f'{i}-ld' for i in cls.platform_prefixes] + ['ld'], 'nasm': ['nasm']}


class PlatformX86Mixin(ASMExecutor):
    abi = PTBOX_ABI_X86
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
    abi = PTBOX_ABI_X64
    ld_name = 'ld_x64'
    ld_m = 'elf_x86_64'
    platform_prefixes = ['x86_64-linux-gnu']
    as_platform_flag = '--64'

    qemu_path = env.runtime.qemu_x64
    dynamic_linker = env.runtime['ld.so_x64'] or '/lib64/ld-linux-x86-64.so.2'
    crt_pre = env.runtime.crt_pre_x64 or ['/usr/lib/x86_64-linux-gnu/crt1.o', '/usr/lib/x86_64-linux-gnu/crti.o']
    crt_post = env.runtime.crt_post_x64 or ['/usr/lib/x86_64-linux-gnu/crtn.o']


class PlatformARMMixin(ASMExecutor):
    abi = PTBOX_ABI_ARM
    ld_name = 'ld_arm'
    ld_m = 'armelf_linux_eabi'
    platform_prefixes = ['arm-linux-gnueabihf']

    qemu_path = env.runtime.qemu_arm
    dynamic_linker = env.runtime['ld.so_arm'] or '/lib/ld-linux-armhf.so.3'
    crt_pre = env.runtime.crt_pre_arm or ['/usr/lib/arm-linux-gnueabihf/crt1.o', '/usr/lib/arm-linux-gnueabihf/crti.o']
    crt_post = env.runtime.crt_post_arm or ['/usr/lib/arm-linux-gnueabihf/crtn.o']


class PlatformARM64Mixin(ASMExecutor):
    abi = PTBOX_ABI_ARM64
    ld_name = 'ld_arm'
    ld_m = 'aarch64linux'
    platform_prefixes = ['aarch64-linux-gnu']

    qemu_path = env.runtime.qemu_arm64
    dynamic_linker = env.runtime['ld.so_arm64'] or '/lib/ld-linux-aarch64.so.1'
    crt_pre = env.runtime.crt_pre_arm or ['/usr/lib/aarch64-linux-gnu/crt1.o', '/usr/lib/aarch64-linux-gnu/crti.o']
    crt_post = env.runtime.crt_post_arm or ['/usr/lib/aarch64-linux-gnu/crtn.o']


NativeMixin: Any = (
    [cls for cls in (PlatformX86Mixin, PlatformX64Mixin, PlatformARMMixin, PlatformARM64Mixin) if cls.abi == NATIVE_ABI]
    or [ASMExecutor]
)[0]
