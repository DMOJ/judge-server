from collections import deque
import re

from .base_executor import BaseExecutor
from result import Result

retraceback = re.compile(r'Traceback \(most recent call last\):\n.*?\n([a-zA-Z_]\w*)(?::[^\n]*?)?$', re.S | re.M)


class PythonExecutor(BaseExecutor):
    loader_script = '''\
import runpy, sys, os
del sys.argv[0]
sys.stdin = os.fdopen(0, 'r', 65536)
sys.stdout = os.fdopen(1, 'w', 65536)
runpy.run_path(sys.argv[0], run_name='__main__')\
'''
    address_grace = 131072
    ext = '.py'

    def __init__(self, problem_id, source_code):
        super(PythonExecutor, self).__init__(problem_id, source_code)

    def get_cmdline(self):
        return [self.get_command(), '-BS', self._loader, self._code]

    def create_files(self, problem_id, source_code):
        self._loader = self._file('-loader.py')
        with open(self._code, 'wb') as fo, open(self._loader, 'wb') as loader:
            # UTF-8 BOM instead of comment to not modify line numbers.
            fo.write('\xef\xbb\xbf')
            fo.write(source_code)
            loader.write(self.loader_script)

    def get_feedback(self, stderr, result):
        if not result.result_flag & Result.IR or not stderr or len(stderr) > 2048:
            return ''
        match = deque(retraceback.finditer(stderr), maxlen=1)
        if not match:
            return ''
        exception = match[0].group(1)
        return '' if len(exception) > 20 else exception
