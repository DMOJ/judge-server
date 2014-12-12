import os
import re
from subprocess import Popen, PIPE
import sys
from communicate import safe_communicate, OutputLimitExceeded
from error import CompileError
from .utils import test_executor

from .resource_proxy import ResourceProxy
from judgeenv import env

try:
    from winutils import max_memory, execution_time
except ImportError:
    windows = False
    max_memory, execution_time = None, None
else:
    windows = True

recomment = re.compile(r'/\*.*?\*/', re.DOTALL)
restring = re.compile(r'''(["'])(?:\\.|[^"\\])*\1''', re.DOTALL)
reinline_comment = re.compile('//.*$', re.MULTILINE)
reclass = re.compile(r'\bpublic\s+class\s+([_a-zA-Z\$][_0-9a-zA-z\$]*?)\b')
repackage = re.compile(r'\bpackage\s+([^.;]+(?:\.[^.;]+)*?);')
JAVA_EXECUTOR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'java_executor.jar'))


def find_class(source):
    source = reinline_comment.sub('', restring.sub('', recomment.sub('', source)))
    class_name = reclass.search(source)
    if class_name is None:
        raise CompileError('No public class')
    package = repackage.search(source)
    if package:
        raise CompileError('Invalid package %s: do not declare package' % package.group(1))
    return class_name


class JavaPopen(object):
    def __init__(self, args, executable, cwd, time_limit, memory_limit, statefile):
        self.process = Popen(args, executable=executable, cwd=cwd,
                                        stdin=PIPE, stdout=PIPE, stderr=PIPE)
        self.execution_time, self.tle = None, None
        self.max_memory, self.mle = None, None
        self.stderr = None
        self.error_info, self.error = None, None
        self.returncode = None
        self.feedback = None
        self.time_limit = time_limit
        self.memory_limit = memory_limit
        self.statefile = statefile
        self._killed = False

    def communicate(self, stdin=None):
        return self._communicate(*self.process.communicate(stdin))

    def _update_windows_stats(self):
        handle = int(self.process._handle)
        self.execution_time = execution_time(handle)
        self.tie = self.execution_time > self.time_limit
        self.max_memory = max_memory(handle) / 1024.
        self.mle = self.max_memory > self.memory_limit
        if self.returncode is None:
            self.returncode = self.process.returncode

    def safe_communicate(self, stdin=None, outlimit=None, errlimit=None):
        try:
            return self._communicate(*safe_communicate(self.process, stdin, outlimit, errlimit))
        except OutputLimitExceeded:
            self.execution_time = 0
            self.tle = 0
            self.max_memory = 0
            self.mle = 0
            self.returncode = -1
            raise

    def _communicate(self, stdout, stderr_):
        try:
            with open(self.statefile, 'r') as proc:
                self.error_info = proc.read()
        except:
            return stdout, None
        try:
            data = self.error_info.split(None, 5)
            self.execution_time, self.tle, self.max_memory, self.mle, self.returncode = map(int, data[:5])
            self.feedback = data[5]
        except:
            if not windows:
                print>> sys.stderr, stderr_
                if self._killed:
                    return stdout, None
                raise
        if windows:
            self._update_windows_stats()
        else:
            self.execution_time /= 1000.0
        if self.returncode == -1:
            self.returncode = 1
        if self.error_info:
            print>> sys.stderr, self.error_info
        if self.feedback == 'OK':
            self.feedback = None
        return stdout, None

    def kill(self):
        self._killed = True
        return self.process.kill()

    @property
    def r_execution_time(self):
        return self.execution_time

    def __getattr__(self, attr):
        return getattr(self.process, attr)


class Executor(ResourceProxy):
    def __init__(self, problem_id, source_code):
        super(Executor, self).__init__()
        class_name = find_class(source_code)
        source_code_file = self._file('%s.java' % class_name.group(1))
        with open(source_code_file, 'wb') as fo:
            fo.write(source_code)
        javac_args = [env['runtime']['javac'], source_code_file]
        javac_process = Popen(javac_args, stderr=PIPE, cwd=self._dir)
        _, compile_error = javac_process.communicate()
        if javac_process.returncode != 0:
            if 'is public, should be declared in a file named' in compile_error:
                raise CompileError('You are a troll. Trolls are not welcome. '
                                   'As a judge, I sentence your code to death.')
            raise CompileError(compile_error)
        self._class_name = class_name.group(1)
        self.warning = compile_error
        self.statefile = self._file('state')

    def launch(self, *args, **kwargs):
        return JavaPopen(['java', '-client',
                          '-Xmx%sK' % kwargs.get('memory'), '-jar', JAVA_EXECUTOR, self._dir,
                          self._class_name, str(kwargs.get('time') * 1000), 'state'] + list(args),
                         executable=env['runtime']['java'], cwd=self._dir,
                         time_limit=kwargs.get('time'), memory_limit=kwargs.get('memory'), statefile=self.statefile)

    def launch_unsafe(self, *args, **kwargs):
        return Popen(['java', '-client', self._class_name] + list(args),
                     executable=env['runtime']['java'],
                     cwd=self._dir,
                     **kwargs)


def initialize():
    if 'java' not in env['runtime']:
        return False
    if not os.path.isfile(env['runtime']['java']):
        return False
    return test_executor('JAVA', Executor, '''\
public class self_test {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
''', problem='self_test')
