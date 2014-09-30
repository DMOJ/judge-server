import os
import re
import subprocess
import sys
from error import CompileError
from executors.utils import test_executor

from .resource_proxy import ResourceProxy
from judgeenv import env

recomment = re.compile(r'/\*.*?\*/', re.DOTALL)
restring = re.compile(r'''(["'])(?:\\.|[^"\\])*\1''', re.DOTALL)
reclass = re.compile(r'\bpublic\s+class\s+([_a-zA-Z][_0-9a-zA-z]+?)\b')
JAVA_EXECUTOR = os.path.join(os.path.dirname(__file__), 'java_executor.jar')


def find_class(source):
    source = restring.sub('', recomment.sub('', source))
    class_name = reclass.search(source)
    if class_name is None:
        raise CompileError('No public class')
    return class_name


class JavaPopen(object):
    def __init__(self, args, executable, cwd):
        self.process = subprocess.Popen(args, executable=executable, cwd=cwd,
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.execution_time, self.tle = None, None
        self.max_memory, self.mle = None, None
        self.stderr = None
        self.error_info, self.error = None, None
        self.returncode = None

    def communicate(self, stdin=None):
        stdout, stderr = self.process.communicate(stdin)
        print>>sys.stderr, stderr
        stderr = stderr.rstrip().split('\n')
        self.error_info = '\n'.join(stderr[:-1])
        self.execution_time, self.tle, self.max_memory, self.mle, self.returncode = map(int, stderr[-1].split())
        self.execution_time /= 1000.0
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
        javac_process = subprocess.Popen(javac_args, stderr=subprocess.PIPE, cwd=self._dir)
        _, compile_error = javac_process.communicate()
        if javac_process.returncode != 0:
            if 'is public, should be declared in a file named' in compile_error:
                raise CompileError('You are a troll. Trolls are not welcome. '
                                   'As a judge, I sentence your code to death.')
            raise CompileError(compile_error)
        self._class_name = class_name.group(1)

    def launch(self, *args, **kwargs):
        return JavaPopen(['java', '-client',
                          '-Xmx%sK' % kwargs.get('memory'), '-jar', JAVA_EXECUTOR, self._dir,
                          self._class_name, str(kwargs.get('time') * 1000)] + list(args),
                         executable=env['runtime']['java'], cwd=self._dir)


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