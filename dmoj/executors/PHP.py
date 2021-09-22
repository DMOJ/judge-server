from typing import List

from dmoj.executors.script_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = 'php'
    command = 'php'
    command_paths = ['php7', 'php5', 'php']

    test_program = '<?php while($f = fgets(STDIN)) echo $f;'

    def get_cmdline(self, **kwargs) -> List[str]:
        return ['php', self._code]
