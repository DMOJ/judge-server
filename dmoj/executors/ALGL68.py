from typing import List

from dmoj.cptbox.handlers import ACCESS_EACCES
from dmoj.executors.compiled_executor import CompiledExecutor


class Executor(CompiledExecutor):
    ext = 'a'
    command = 'a68g'

    test_program = """
BEGIN
    STRING input;
    get(standin, input);
    print((input, newline))
END
"""

    data_grace = 131072
    syscalls = [
        ('mkdir', ACCESS_EACCES),
        ('mkdirat', ACCESS_EACCES),
        'alarm',
        'setitimer',
    ]

    def get_compile_args(self) -> List[str]:
        command = self.get_command()
        assert command is not None
        assert self._code is not None
        # This doesn't actually compile anything, but will generate useful
        # output if the program is malformed.
        return [command, '--norun', '--noportcheck', '--nopragmats', self._code]

    def get_cmdline(self, **kwargs) -> List[str]:
        command = self.get_command()
        assert command is not None
        assert self._code is not None
        return [command, '--nowarnings', '--noportcheck', '--nopragmats', self._code]

    def get_executable(self):
        return self.get_command()
