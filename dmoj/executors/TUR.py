import os

from dmoj.executors.compiled_executor import CompiledExecutor
from dmoj.judgeenv import env


class Executor(CompiledExecutor):
    ext = 't'
    name = 'TUR'
    command = 'tprolog'
    test_program = '''\
var echo : string
get echo : *
put echo
'''

    def get_fs(self):
        return super().get_fs() + [self._code + 'bc']

    def get_compile_args(self):
        tprologc = self.runtime_dict['tprologc']
        return [tprologc, self._code, os.path.dirname(tprologc)]

    def get_cmdline(self):
        return [self.runtime_dict['tprolog'], self._code + 'bc']

    def get_executable(self):
        return self.get_command()

    @classmethod
    def initialize(cls):
        if 'tprolog' not in env['runtime'] or 'tprologc' not in env['runtime']:
            return False
        return super().initialize()

    @classmethod
    def get_find_first_mapping(cls):
        return {
            'tprolog': ['tprolog'],
            'tprologc': ['tprologc'],
        }
