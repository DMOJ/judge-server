from dmoj.executors.base_executor import ScriptExecutor


class Executor(ScriptExecutor):
    name = 'PHP'
    ext = '.php'
    command = 'php'
    command_paths = ['php7', 'php5', 'php']

    fs = ['.*/php[\w-]*\.ini$', '.*/conf.d/.*\.ini$']

    test_program = '<?php while($f = fgets(STDIN)) echo $f;'

    def get_cmdline(self):
        return ['php', self._code]
