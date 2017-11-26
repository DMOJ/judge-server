import os

from dmoj.executors.mixins import ScriptDirectoryMixin
from .base_executor import ScriptExecutor

if os.name != 'nt':
    from dmoj.cptbox.handlers import ACCESS_DENIED


class Executor(ScriptDirectoryMixin, ScriptExecutor):
    ext = '.R'
    name = 'R'
    nproc = -1  # needs a bunch
    command = 'Rscript'
    test_program = 'writeLines(readLines(file("stdin")))'

    if os.name != 'nt':
        syscalls = ['mkdir', 'setup', 'fork', 'waitpid', 'wait4', 'getpgrp', 'execve',
                    ('statfs64', ACCESS_DENIED), ('statfs', ACCESS_DENIED), 'newfstatat', 'unlinkat', 'openat']

    fs = ['/etc/passwd$', '/etc/nsswitch.conf$', '/etc/group$', '/usr/lib/R/.*$', '/usr/share/locale/locale.alias$', '/sys/devices/system/cpu$', '/proc/filesystems$']

    def get_cmdline(self):
        return [self.get_command(), '--vanilla', self._code]
