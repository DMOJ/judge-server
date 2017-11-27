from dmoj.executors.base_executor import ScriptExecutor
from dmoj.executors.mixins import ScriptDirectoryMixin


class Executor(ScriptDirectoryMixin, ScriptExecutor):
    ext = '.m'
    name = 'OCTAVE'
    command = 'octave'
    address_grace = 262144
    test_program = "disp(input('', 's'))"

    fs = ['/etc/fltk/']

    def get_cmdline(self):
        return [self.get_command(), '--no-gui', '--no-history', '--no-init-file', '--no-site-file',
                '--no-window-system', '--norc', '--quiet', self._code]

    @classmethod
    def get_find_first_mapping(cls):
        return {
            'octave': ['octave-cli'],
        }
