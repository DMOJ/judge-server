import os
import shutil

from dmoj.cptbox.filesystem_policies import ExactFile
from dmoj.cptbox.isolate import DeniedSyscall, protection_fault
from dmoj.executors.script_executor import ScriptExecutor


class ShellExecutor(ScriptExecutor):
    nproc = -1
    shell_commands = ['cat', 'grep', 'awk', 'perl']

    def get_shell_commands(self):
        return self.shell_commands

    def get_allowed_exec(self):
        return list(map(shutil.which, self.get_shell_commands()))

    def get_fs(self):
        return super().get_fs() + list(map(ExactFile, self.get_allowed_exec()))

    def get_allowed_syscalls(self):
        return super().get_allowed_syscalls() + ['fork', 'waitpid', 'wait4']

    def get_security(self, launch_kwargs=None):
        from dmoj.cptbox.syscalls import sys_execve, sys_access, sys_eaccess

        sec = super().get_security(launch_kwargs)
        allowed = set(self.get_allowed_exec())

        def handle_execve(debugger) -> None:
            path = sec.get_full_path_unnormalized(debugger, debugger.readstr(debugger.uarg0))
            path = '/' + os.path.normpath(path).lstrip('/')
            if path not in allowed:
                raise DeniedSyscall(protection_fault, f'Not allowed to use command: {path}')

        sec[sys_execve] = handle_execve
        sec[sys_eaccess] = sec[sys_access]
        return sec

    def get_env(self):
        env = super().get_env()
        env['PATH'] = os.environ['PATH']
        return env
