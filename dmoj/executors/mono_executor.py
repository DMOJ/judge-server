import os
import re
from collections import deque
from typing import Dict, List, Optional

from dmoj.cptbox import TracedPopen
from dmoj.cptbox.filesystem_policies import RecursiveDir
from dmoj.cptbox.handlers import ACCESS_EAGAIN
from dmoj.executors.compiled_executor import CompiledExecutor
from dmoj.result import Result
from dmoj.utils.unicode import utf8text

reexception = re.compile(r'\bFATAL UNHANDLED EXCEPTION: (.*?):', re.U)


class MonoTracedPopen(TracedPopen):
    def _cpu_time_exceeded(self):
        pass


class MonoExecutor(CompiledExecutor):
    nproc = -1
    address_grace = 262144
    # Give Mono access to 64mb more data segment memory. This is a hack, for
    # dealing with the fact that Mono behaves extremely poorly when handling
    # out-of-memory situations -- in many cases, it dumps an assertion to
    # standard error, then *exits with a 0 exit code*. Unfortunately, it will
    # only infrequently throw a System.OutOfMemoryException.
    #
    # The hope here is that if a problem allows X mb of memory and we cap at
    # X+64 mb, if an OOM situation occurs, it will occur at a point where
    # VmHWM >= X. Then, even if Mono exits poorly, the submission will still
    # get flagged as MLE.
    data_grace = 65536
    cptbox_popen_class = MonoTracedPopen
    fs = [RecursiveDir('/etc/mono')]
    compiler_read_fs = fs
    # Mono sometimes forks during its crashdump procedure, but continues even if
    # the call to fork fails.
    syscalls = [
        'wait4',
        'rt_sigsuspend',
        'msync',
        'fadvise64',
        'clock_nanosleep',
        ('fork', ACCESS_EAGAIN),
    ]

    def get_env(self) -> Dict[str, str]:
        env = super().get_env()
        # Disable Mono's usage of /dev/shm, so we don't have to deal with
        # its extremely messy access patterns to it.
        env['MONO_DISABLE_SHARED_AREA'] = '1'
        # Disable Mono's generation of core dump files (e.g. on MLE).
        env['MONO_CRASH_NOFILE'] = '1'
        return env

    def get_compiled_file(self) -> str:
        return self._file('%s.exe' % self.problem)

    def get_cmdline(self, **kwargs) -> List[str]:
        assert self._executable is not None
        return ['mono', self._executable]

    def get_executable(self) -> str:
        return self.runtime_dict['mono']

    @classmethod
    def get_find_first_mapping(cls) -> Optional[Dict[str, List[str]]]:
        res = super().get_find_first_mapping()
        if res:
            res['mono'] = ['mono']
        return res

    def populate_result(self, stderr: bytes, result: Result, process: TracedPopen) -> None:
        super().populate_result(stderr, result, process)
        if process.is_ir and b'Garbage collector could not allocate' in stderr:
            result.result_flag |= Result.MLE

    def parse_feedback_from_stderr(self, stderr: bytes, process: TracedPopen) -> str:
        match = deque(reexception.finditer(utf8text(stderr, 'replace')), maxlen=1)
        if not match:
            return ''

        exception = match[0].group(1)
        return exception

    @classmethod
    def initialize(cls) -> bool:
        if 'mono' not in cls.runtime_dict or not os.path.isfile(cls.runtime_dict['mono']):
            return False
        return super().initialize()
