import os
import re
from collections import deque

import six

from dmoj.judgeenv import env
from dmoj.result import Result
from dmoj.utils.unicode import utf8bytes, utf8text
from .base_executor import CompiledExecutor

GCC_ENV = env.runtime.gcc_env or {}
GCC_COMPILE = os.environ.copy()
IS_ARM = hasattr(os, 'uname') and os.uname()[4].startswith('arm')

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
    has_color = False

    def create_files(self, problem_id, main_source, **kwargs):
        aux_sources = kwargs.get('aux_sources', {})
        fds = kwargs.get('fds', None)
        writable = kwargs.get('writable', (1, 2))
        aux_sources[problem_id + self.ext] = main_source

        sources = []
        for name, source in aux_sources.items():
            if '.' not in name:
                name += self.ext
            with open(self._file(name), 'wb') as fo:
                fo.write(utf8bytes(source))
            sources.append(name)
        self.sources = sources
        self._fds = fds
        self._writable = writable
        self.defines = kwargs.get('defines', [])

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
                self.sources + self.get_defines() + ['-O2', '-lm'] + ([] if IS_ARM else ['-march=native']) +
                self.get_flags() + self.get_ldflags() + ['-s', '-o', self.get_compiled_file()])

    def get_compile_env(self):
        return GCC_COMPILE

    def get_security(self, launch_kwargs=None):
        from dmoj.cptbox import CHROOTSecurity
        return self._add_syscalls(
            CHROOTSecurity(self.get_fs(), writable=self._writable,
                           io_redirects=launch_kwargs.get('io_redirects', None))
        )

    def get_env(self):
        return GCC_ENV

    def get_feedback(self, stderr, result, process):
        if not result.result_flag & Result.RTE or not stderr or len(stderr) > 2048:
            return ''
        match = deque(recppexc.finditer(stderr), maxlen=1)
        if not match:
            return ''
        exception = match[0].group(1)
        return '' if len(exception) > 40 else utf8text(exception, 'replace')

    @classmethod
    def get_version_flags(cls, command):
        return ['-dumpversion']

    @classmethod
    def autoconfig(cls):
        return super(GCCExecutor, cls).autoconfig()

    @classmethod
    def initialize(cls, sandbox=True):
        res = super(CompiledExecutor, cls).initialize(sandbox=sandbox)
        if res:
            cls.has_color = cls.get_runtime_versions()[0][1] > (4, 9)
        return res
