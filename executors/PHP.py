from .base_executor import ScriptExecutor
from judgeenv import env


class Executor(ScriptExecutor):
    ext = '.php'
    name = 'PHP'
    command = env['runtime'].get('php')
    address_grace = 131072
    test_program = '<?php while($f = fgets(STDIN)) echo $f;'
    fs = ['.*\.so', '/etc/localtime$', '.*/php[\w-]*\.ini$']
    if 'phpconfdir' in env['runtime']:
        fs += [env['runtime']['phpconfdir']]

    def get_cmdline(self):
        return ['php', self._code]

    def get_fs(self):
        return self.fs + [self._code]


initialize = Executor.initialize