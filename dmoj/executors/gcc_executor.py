import os
import re
from collections import deque

from dmoj.judgeenv import env
from dmoj.result import Result
from dmoj.utils.unicode import utf8bytes, utf8text
from .base_executor import CompiledExecutor

GCC_ENV = env.runtime.gcc_env or {}
GCC_COMPILE = os.environ.copy()

if os.name == 'nt':
    GCC_COMPILE.update((k.encode('mbcs'), v.encode('mbcs')) for k, v in
                       (env.runtime.gcc_compile or GCC_ENV).iteritems())
    GCC_ENV = dict((k.encode('mbcs'), v.encode('mbcs')) for k, v in GCC_ENV.iteritems())
else:
    GCC_COMPILE.update(env.runtime.gcc_compile or {})

recppexc = re.compile(br"terminate called after throwing an instance of \'([A-Za-z0-9_:]+)\'\r?$", re.M)


class GCCExecutor(CompiledExecutor):
    defines = []
    flags = []
    name = 'GCC'
    arch = 'gcc_target_arch'
    has_color = False

    def __init__(self, problem_id, main_source, **kwargs):
        super(GCCExecutor, self).__init__(problem_id, main_source, **kwargs)

        self.source_dict = kwargs.get('aux_sources', {})
        if main_source:
            self.source_dict[problem_id + self.ext] = main_source
        self.defines = kwargs.get('defines', [])

    def create_files(self, problem_id, main_source, **kwargs):
        self.source_paths = []
        for name, source in self.source_dict.items():
            if '.' not in name:
                name += self.ext
            with open(self._file(name), 'wb') as fo:
                fo.write(utf8bytes(source))
            self.source_paths.append(name)

    def get_binary_cache_key(self):
        key_components = ([self.problem, self.get_command(), self.get_march_flag()] +
                          self.get_defines() + self.get_flags() + self.get_ldflags() +
                          list(self.source_dict.values()))
        return ''.join(key_components)

    def get_ldflags(self):
        if os.name == 'nt':
            return ['-Wl,--stack,67108864']
        return []

    def get_flags(self):
        return self.flags

    def get_defines(self):
        defines = ['-DONLINE_JUDGE'] + self.defines
        if os.name == 'nt':
            defines.append('-DWIN32')
        return defines

    def get_compile_args(self):
        return ([self.get_command(), '-Wall'] + (['-fdiagnostics-color=always'] if self.has_color else []) +
                self.source_paths + self.get_defines() + ['-O2', '-lm', self.get_march_flag()] +
                self.get_flags() + self.get_ldflags() + ['-s', '-o', self.get_compiled_file()])

    def get_compile_env(self):
        return GCC_COMPILE

    def get_env(self):
        env = super(GCCExecutor, self).get_env() or {}
        env.update(GCC_ENV)
        return env

    def get_feedback(self, stderr, result, process):
        if not result.result_flag & Result.RTE or not stderr or len(stderr) > 2048:
            return ''
        match = deque(recppexc.finditer(stderr), maxlen=1)
        if not match:
            return ''
        exception = match[0].group(1)
        return '' if len(exception) > 40 else utf8text(exception, 'replace')

    @classmethod
    def get_march_flag(cls):
        conf_arch = cls.runtime_dict.get(cls.arch, 'native')
        if conf_arch:
            return '-march=%s' % conf_arch
        # arch must've been explicitly disabled
        return ''

    @classmethod
    def get_version_flags(cls, command):
        return ['-dumpversion']

    @classmethod
    def autoconfig_run_test(cls, result):
        # Some versions of GCC/Clang (like those in Raspbian or ARM64 Debian)
        # can't autodetect the CPU, in which case our unconditional passing of
        # -march=native breaks. Here we try to see if -march=native works, and
        # if not fall back to a generic (slow) build.
        for target in ['native', None]:
            result[cls.arch] = target
            executor = type('Executor', (cls,), {'runtime_dict': result})
            executor.__module__ = cls.__module__
            errors = []
            success = executor.run_self_test(output=False, error_callback=errors.append)
            if success:
                message = 'Using %s (%s target)' % (result[cls.command], target or 'generic')
                # Don't pollute the YAML in the default case
                if target == 'native':
                    del result[cls.arch]
                return result, success, message, None
        return result, success, 'Failed self-test', '\n'.join(errors)

    @classmethod
    def autoconfig(cls):
        return super(GCCExecutor, cls).autoconfig()

    @classmethod
    def initialize(cls, sandbox=True):
        res = super(CompiledExecutor, cls).initialize(sandbox=sandbox)
        if res:
            cls.has_color = cls.get_runtime_versions()[0][1] > (4, 9)
        return res
