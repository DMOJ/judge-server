import os
import re
import subprocess
from communicate import safe_communicate
from error import CompileError
from executors.resource_proxy import ResourceProxy
from judgeenv import env
from winutils import execution_time, max_memory


reexc = re.compile(r'E1AE1B1F-C5FE-4335-B642-9446634350A0:\r?\n(.*?):')


class CLRProcess(object):
    csbox = os.path.join(os.path.dirname(__file__), 'csbox.exe')

    def __init__(self, executable, dir, time, memory):
        self.process = subprocess.Popen([self.csbox, dir, executable], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=dir)
        self.time_limit = time
        self.memory_limit = memory
        self.tle = None
        self.execution_time = None
        self.mle = None
        self.max_memory = None
        self.execution_time = None
        self.feedback = None
        self.returncode = None

    @property
    def r_execution_time(self):
        return self.execution_time

    def __getattr__(self, attr):
        return getattr(self.process, attr)

    def _update_stats(self):
        handle = int(self.process._handle)
        self.execution_time = execution_time(handle)
        self.tie = self.execution_time > self.time_limit
        self.max_memory = max_memory(handle) / 1024.
        self.mle = self.max_memory > self.memory_limit
        self.returncode = self.process.returncode

    def _find_exception(self, stderr):
        if len(stderr) < 8192:
            match = reexc.search(stderr)
            return match and match.group(1)

    def communicate(self, stdin=None):
        try:
            stdout, stderr = self.process.communicate(stdin)
            self.feedback = self._find_exception(stderr)
            return stdout, stderr
        finally:
            self._update_stats()

    def safe_communicate(self, stdin=None, outlimit=None, errlimit=None):
        try:
            stdout, stderr = safe_communicate(self.process, stdin, outlimit, errlimit)
            self.feedback = self._find_exception(stderr)
            return stdout, stderr
        finally:
            self._update_stats()


class CLRExecutor(ResourceProxy):
    extension = None
    compiler = None

    def __init__(self, problem_id, source_code):
        super(CLRExecutor, self).__init__()
        source_code_file = self._file('%s.%s' % (problem_id, self.extension))
        self.name = self._file('%s.exe' % problem_id)
        with open(source_code_file, 'wb') as fo:
            fo.write(source_code)

        csc_args = [env['runtime'][self.compiler], '-nologo', '-out:%s' % self.name, source_code_file]

        csc_process = subprocess.Popen(csc_args, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, cwd=self._dir)
        compile_error, _ = csc_process.communicate()
        if csc_process.returncode != 0:
            raise CompileError(compile_error)
        self.warning = compile_error

    def launch(self, *args, **kwargs):
        return CLRProcess(self.name, self._dir, kwargs.get('time'), kwargs.get('memory'))

    def launch_unsafe(self, *args, **kwargs):
        return subprocess.Popen([self.name] + list(args), cwd=self._dir, **kwargs)