from collections import deque
from .resource_proxy import ResourceProxy

try:
    from cptbox import SecurePopen, PIPE
except ImportError:
    SecurePopen, PIPE = None, None
    from wbox import WBoxPopen
from subprocess import Popen
import re
from result import Result

retraceback = re.compile(r'Traceback \(most recent call last\):\n.*?\n([a-zA-Z_]\w*)(?::[^\n]*?)?$', re.S | re.M)


class PythonExecutor(ResourceProxy):
    loader_script = '''\
import runpy, sys, os
del sys.argv[0]
sys.stdin = os.fdopen(0, 'r', 65536)
sys.stdout = os.fdopen(1, 'w', 65536)
runpy.run_path(sys.argv[0], run_name='__main__')\
'''

    def __init__(self, problem_id, source_code):
        super(PythonExecutor, self).__init__()
        self._script = source_code_file = self._file('%s.py' % problem_id)
        self._loader = self._file('-loader.py')
        with open(source_code_file, 'wb') as fo, open(self._loader, 'wb') as loader:
            # UTF-8 BOM instead of comment to not modify line numbers.
            fo.write('\xef\xbb\xbf')
            fo.write(source_code)
            loader.write(self.loader_script)

    def get_security(self):
        raise NotImplementedError()

    def get_executable(self):
        raise NotImplementedError()

    def get_argv0(self):
        return 'python'

    if SecurePopen is None:
        def launch(self, *args, **kwargs):
            return WBoxPopen([self.get_argv0(), '-BS', self._loader, self._script] + list(args),
                             time=kwargs.get('time'), memory=kwargs.get('memory'),
                             cwd=self._dir, executable=self.get_executable(),
                             network_block=True)
    else:
        def launch(self, *args, **kwargs):
            return SecurePopen([self.get_executable(), '-BS', self._loader, self._script] + list(args),
                               security=self.get_security(), address_grace=131072,
                               time=kwargs.get('time'), memory=kwargs.get('memory'),
                               stderr=(PIPE if kwargs.get('pipe_stderr', False) else None),
                               env={'LANG': 'C'}, cwd=self._dir)

    def launch_unsafe(self, *args, **kwargs):
        return Popen([self.get_argv0(), '-BS', self._loader, self._script] + list(args),
                     env={'LANG': 'C'}, executable=self.get_executable(),
                     cwd=self._dir, **kwargs)

    def get_feedback(self, stderr, result):
        if not result.result_flag & Result.IR or not stderr or len(stderr) > 2048:
            return ''
        match = deque(retraceback.finditer(stderr), maxlen=1)
        if not match:
            return ''
        exception = match[0].group(1)
        return '' if len(exception) > 20 else exception
