from dmoj.executors.script_executor import ScriptExecutor


class Executor(ScriptExecutor):
    name = 'PHP'
    ext = 'php'
    command = 'php'
    command_paths = ['php7', 'php5', 'php']

    fs = [r'.*/php[\w-]*\.ini$', r'.*/conf.d/.*\.ini$']

    test_program = '<?php while($f = fgets(STDIN)) echo $f;'

    def get_cmdline(self):
        return ['php', self._code]
