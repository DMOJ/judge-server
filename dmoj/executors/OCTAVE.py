from .base_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = '.m'
    name = 'OCTAVE'
    command = 'octave'
    address_grace = 131072
    test_program = "disp(input('', 's'))"

    fs = ['.*\.m', '/lib/', '/etc/nsswitch\.conf$', '/etc/passwd$', '/usr/share/', '/etc/fltk/']

    def get_cmdline(self):
        return [self.get_command(), '--no-gui', '--no-history', '--no-init-file', '--no-site-file',
                '--no-window-system', '--norc', '--quiet', self._code]
