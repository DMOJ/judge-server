from typing import List

from dmoj.executors.shell_executor import ShellExecutor


class Executor(ShellExecutor):
    ext = 'sh'
    name = 'BASH'
    command = 'bash'
    test_program = 'exec cat'

    def get_cmdline(self, **kwargs) -> List[str]:
        return ['bash', self._code]
