from typing import List, Tuple

from dmoj.executors.script_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = 'js'
    name = 'V8JS'
    command = 'v8dmoj'
    test_program = 'print(gets());'
    address_grace = 786432
    nproc = -1

    @classmethod
    def get_version_flags(cls, command: str) -> List[Tuple[str, ...]]:
        return [('-e', 'print(version())')]

    def get_cmdline(self, **kwargs) -> List[str]:
        command = self.get_command()
        assert command is not None
        return [command, '--stack-size=131072', self._code]  # 128MB Stack Limit
