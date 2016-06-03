import errno

from .base_executor import ScriptExecutor
from dmoj.judgeenv import env
from dmoj.cptbox.syscalls import *


class Executor(ScriptExecutor):
    ext = '.R'
    name = 'R'
    nproc = -1  # needs a bunch
    command = env['runtime'].get('Rscript')
    test_program = 'writeLines(readLines(file("stdin")))'
    syscalls = ['mkdir', 'setup', 'fork', 'waitpid', 'getpgrp', 'dup2', 'nanosleep',
               'sched_getaffinity', 'execve']

    fs = ['stdin', '.*\.(?:so|rdb|rdx|rds|R)', '/lib/', '/etc/ld\.so\.(?:cache|preload|nohwcap)$', '/proc/stat$',
          '/usr/lib/', '/usr/local/lib/', '/etc/passwd$', '/proc/meminfo$', '/sys/devices/system/cpu/online$',
          '/etc/nsswitch.conf$', '/etc/group$', '/dev/(?:null|urandom|random|tty|stdin|stdout|stderr)$']

    def get_security(self):
        security = super(Executor, self).get_security()

        def handle_socket(debugger):
            def socket_return():
                debugger.result = -errno.EACCES

            debugger.syscall = debugger.getpid_syscall
            debugger.on_return(socket_return)
            return True

        security[sys_socket] = handle_socket
        security[sys_socketcall] = handle_socket
        return security

    def get_cmdline(self):
        return [self.get_command(), '--vanilla', self._code]


initialize = Executor.initialize
