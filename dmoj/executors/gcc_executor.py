import os
import re
from collections import deque
from typing import Any, Dict, List, Optional, Tuple, Type

from dmoj.cptbox import TracedPopen
from dmoj.executors.compiled_executor import CompiledExecutor
from dmoj.executors.mixins import SingleDigitVersionMixin
from dmoj.judgeenv import env
from dmoj.utils.unicode import utf8bytes, utf8text

GCC_ENV = env.runtime.gcc_env or {}
GCC_COMPILE = os.environ.copy()
GCC_COMPILE.update(env.runtime.gcc_compile or {})
MAX_ERRORS = 5

recppexc = re.compile(br"terminate called after throwing an instance of \'([A-Za-z0-9_:]+)\'\r?$", re.M)


class GCCExecutor(SingleDigitVersionMixin, CompiledExecutor):
    defines: List[str] = []
    flags: List[str] = []
    arch = 'gcc_target_arch'
    has_color = False

    source_dict: Dict[str, bytes] = {}

    def __init__(self, problem_id: str, source_code: bytes, **kwargs) -> None:
        self.source_dict = kwargs.pop('aux_sources', {})
        if source_code:
            self.source_dict[problem_id + self.ext] = source_code
        self.defines = kwargs.pop('defines', [])

        super().__init__(problem_id, source_code, **kwargs)

    def create_files(self, problem_id: str, source_code: bytes, *args, **kwargs) -> None:
        self.source_paths = []
        for name, source in self.source_dict.items():
            if '.' not in name:
                name += '.' + self.ext
            with open(self._file(name), 'wb') as fo:
                fo.write(utf8bytes(source))
            self.source_paths.append(name)

    def get_binary_cache_key(self) -> bytes:
        command = self.get_command()
        assert command is not None
        key_components = (
            [self.problem, command, self.get_march_flag()] + self.get_defines() + self.get_flags() + self.get_ldflags()
        )
        return utf8bytes(''.join(key_components)) + b''.join(self.source_dict.values())

    def get_ldflags(self) -> List[str]:
        return []

    def get_flags(self) -> List[str]:
        return self.flags + [f'-fmax-errors={MAX_ERRORS}']

    def get_defines(self) -> List[str]:
        return ['-DONLINE_JUDGE'] + self.defines

    def get_compile_args(self) -> List[str]:
        command = self.get_command()
        assert command is not None
        return (
            [command, '-Wall']
            + (['-fdiagnostics-color=always'] if self.has_color else [])
            + self.source_paths
            + self.get_defines()
            + ['-O2', '-lm', self.get_march_flag()]
            + self.get_flags()
            + self.get_ldflags()
            + ['-s', '-o', self.get_compiled_file()]
        )

    def get_compile_env(self) -> Optional[Dict[str, str]]:
        return GCC_COMPILE

    def get_env(self) -> Dict[str, str]:
        env = super().get_env() or {}
        env.update(GCC_ENV)
        return env

    def parse_feedback_from_stderr(self, stderr: bytes, process: TracedPopen) -> str:
        if not stderr or len(stderr) > 2048:
            return ''
        match = deque(recppexc.finditer(stderr), maxlen=1)
        if not match:
            return ''
        exception = match[0].group(1)
        return '' if len(exception) > 40 else utf8text(exception, 'replace')

    @classmethod
    def get_march_flag(cls) -> str:
        conf_arch = cls.runtime_dict.get(cls.arch, 'native')
        if conf_arch:
            return f'-march={conf_arch}'
        # arch must've been explicitly disabled
        return ''

    @classmethod
    def get_version_flags(cls, command: str) -> List[str]:
        return ['-dumpversion']

    @classmethod
    def autoconfig_run_test(cls, result: Dict[str, Any]) -> Tuple[Dict[str, str], bool, str, str]:
        # Some versions of GCC/Clang (like those in Raspbian or ARM64 Debian)
        # can't autodetect the CPU, in which case our unconditional passing of
        # -march=native breaks. Here we try to see if -march=native works, and
        # if not fall back to a generic (slow) build.
        for target in ['native', None]:
            result[cls.arch] = target
            executor: Type[GCCExecutor] = type('Executor', (cls,), {'runtime_dict': result})
            executor.__module__ = cls.__module__
            errors: List[str] = []
            success = executor.run_self_test(output=False, error_callback=errors.append)
            if success:
                assert cls.command is not None
                message = f'Using {result[cls.command]} ({target or "generic"} target)'
                # Don't pollute the YAML in the default case
                if target == 'native':
                    del result[cls.arch]
                return result, success, message, ''
        return result, success, 'Failed self-test', '\n'.join(errors)

    @classmethod
    def autoconfig(cls) -> Tuple[Optional[Dict[str, Any]], bool, str, str]:
        return super().autoconfig()

    @classmethod
    def initialize(cls) -> bool:
        res = super().initialize()
        if res:
            versions = cls.get_runtime_versions()
            cls.has_color = versions is not None and versions[0][1] is not None and versions[0][1] > (4, 9)
        return res
