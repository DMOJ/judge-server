from dmoj.executors.compiled_executor import CompiledExecutor
from dmoj.judgeenv import env


class Executor(CompiledExecutor):
    ext = 't'
    name = 'TUR'
    command = 'tprologc'
    test_program = '''\
var echo : string
get echo : *
put echo
'''

    def get_fs(self):
        return super().get_fs() + [self._code + 'bc']

    def get_compile_args(self):
        return [self.get_command(), self._code, env['runtime']['turing_dir']]

    def get_cmdline(self):
        return [env['runtime']['tprolog'], self._code + 'bc']

    def get_executable(self):
        return None

    @classmethod
    def get_runtime_versions(cls):
        return ('tprologc', (1, 0, 0)),

    @classmethod
    def initialize(cls):
        if 'tprolog' not in env['runtime'] or 'tprologc' not in env['runtime'] or 'turing_dir' not in env['runtime']:
            return False
        return super().initialize()
