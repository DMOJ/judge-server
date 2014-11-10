import os
import re
from subprocess import Popen, PIPE
import sys
from communicate import safe_communicate
from error import CompileError
from .utils import test_executor

from .resource_proxy import ResourceProxy
from judgeenv import env

recomment = re.compile(r'/\*.*?\*/', re.DOTALL)
restring = re.compile(r'''(["'])(?:\\.|[^"\\])*\1''', re.DOTALL)
reclass = re.compile(r'\bpublic\s+class\s+([_a-zA-Z][_0-9a-zA-z]*?)\b')
JAVA_EXECUTOR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'java_executor.jar'))


def find_class(source):
    source = restring.sub('', recomment.sub('', source))
    class_name = reclass.search(source)
    if class_name is None:
        raise CompileError('No public class')
    return class_name


class JavaPopen(object):
    def __init__(self, args, executable, cwd):
        self.process = Popen(args, executable=executable, cwd=cwd,
                                        stdin=PIPE, stdout=PIPE, stderr=PIPE)
        self.execution_time, self.tle = None, None
        self.max_memory, self.mle = None, None
        self.stderr = None
        self.error_info, self.error = None, None
        self.returncode = None
        self.feedback = None

    def communicate(self, stdin=None):
        return self._communicate(*self.process.communicate(stdin))

    def safe_communicate(self, stdin=None, outlimit=None, errlimit=None):
        return self._communicate(*safe_communicate(self.process, stdin, outlimit, errlimit))

    def _communicate(self, stdout, stderr_):
        stderr = stderr_.rstrip().split('\n')
        self.error_info = '\n'.join(stderr[:-1]).strip()
        try:
            data = stderr[-1].split(None, 5)
            self.execution_time, self.tle, self.max_memory, self.mle, self.returncode = map(int, data[:5])
            self.feedback = data[6]
        except:
            print>> sys.stderr, stderr_
            raise
        self.execution_time /= 1000.0
        if self.feedback == 'OK':
            self.feedback = None
        if self.returncode == -1:
            self.returncode = 1
        if self.error_info:
            print>> sys.stderr, self.error_info
        return stdout, None

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

    def launch(self, *args, **kwargs):
        return JavaPopen(['java', '-client',
                          '-Xmx%sK' % kwargs.get('memory'), '-jar', JAVA_EXECUTOR, self._dir,
                          self._class_name, str(kwargs.get('time') * 1000)] + list(args),
                         executable=env['runtime']['java'], cwd=self._dir)

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
