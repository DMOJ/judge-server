from collections import deque
import re

import six

from dmoj.executors.mixins import ScriptDirectoryMixin
from .base_executor import ScriptExecutor
from dmoj.result import Result

retraceback = re.compile(r'Traceback \(most recent call last\):\n.*?\n([a-zA-Z_]\w*)(?::[^\n]*?)?$', re.S | re.M)


class PythonExecutor(ScriptDirectoryMixin, ScriptExecutor):
    loader_script = '''\
import runpy, sys, os
del sys.argv[0]
if not sys.stdin.isatty():
    sys.stdin = os.fdopen(0, 'r', 65536)
if not sys.stdout.isatty():
    sys.stdout = os.fdopen(1, 'w', 65536)
runpy.run_path(sys.argv[0], run_name='__main__')\
'''
    address_grace = 131072
    ext = '.py'

    def get_cmdline(self):
        return [self.get_command(), '-BS', self._loader, self._code]

    def get_allowed_syscalls(self):
        syscalls = super(PythonExecutor, self).get_allowed_syscalls()
        syscalls += ['statfs', 'statfs64']
        return syscalls

    def create_files(self, problem_id, source_code):
        self._loader = self._file('-loader.py')
        with open(self._code, 'wb') as fo, open(self._loader, 'w') as loader:
            # UTF-8 BOM instead of comment to not modify line numbers.
            fo.write(b'\xef\xbb\xbf')

            if isinstance(source_code, six.text_type):
                source_code = source_code.encode('utf-8')
            fo.write(source_code)
            loader.write(self.loader_script)

    def get_feedback(self, stderr, result, process):
        if not result.result_flag & Result.IR or not stderr or len(stderr) > 2048:
            return ''
        match = deque(retraceback.finditer(stderr.decode('utf-8')), maxlen=1)
        if not match:
            return ''
        exception = match[0].group(1)
        return '' if len(exception) > 20 else exception

    @classmethod
    def get_version_flags(cls, command):
        return ['-V']
