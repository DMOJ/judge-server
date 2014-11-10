from .resource_proxy import ResourceProxy
from cptbox import SecurePopen, PIPE
from subprocess import Popen


class PythonExecutor(ResourceProxy):
    def __init__(self, problem_id, source_code):
        super(PythonExecutor, self).__init__()
        self._script = source_code_file = self._file('%s.py' % problem_id)
        customize = '''\
# encoding: utf-8
__import__('sys').stdout = __import__('os').fdopen(1, 'w', 65536)
__import__('sys').stdin = __import__('os').fdopen(0, 'r', 65536)
'''
        with open(source_code_file, 'wb') as fo:
            fo.write(customize)
            fo.write(source_code)

    def get_security(self):
        raise NotImplementedError()

    def get_executable(self):
        raise NotImplementedError()

    def launch(self, *args, **kwargs):
        return SecurePopen([self.get_executable(), '-BS', self._script] + list(args),
                           security=self.get_security(),
                           time=kwargs.get('time'),
                           memory=kwargs.get('memory'),
                           address_grace=131072,
                           stderr=(PIPE if kwargs.get('pipe_stderr', False) else None),
                           env={'LANG': 'C'}, cwd=self._dir)

    def launch_unsafe(self, *args, **kwargs):
        return Popen([self.get_executable(), '-BS', self._script] + list(args),
                     env={'LANG': 'C'},
                     cwd=self._dir,
                     **kwargs)
