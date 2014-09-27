import os
import subprocess
import sys
from cptbox import SecurePopen, NullSecurity
from error import CompileError
from executors.utils import test_executor

from .resource_proxy import ResourceProxy
from judgeenv import env


JAVA_EXECUTOR = os.path.join(os.path.dirname(__file__), 'java_executor.jar')


class JavaPopen(object):
    def __init__(self, args, executable):
        self.process = subprocess.Popen(args, executable=executable,
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.execution_time, self.tle = None, None
        self.max_memory, self.mle = None, None
        self.stderr = None
        self.error_info, self.error = None, None
        self.returncode = None

    def communicate(self, stdin=None):
        stdout, stderr = self.process.communicate(stdin)
        stderr = stderr.rstrip().split('\n')
        self.error_info = '\n'.join(stderr[:-1])
        self.execution_time, self.tle, self.max_memory, self.mle, self.returncode = map(int, stderr[-1].split())
        self.execution_time /= 1000.0
        print>>sys.stderr, stderr
        return stdout, None

    @property
    def r_execution_time(self):
        return self.execution_time

    def __getattr__(self, attr):
        return getattr(self.process, attr)


class Executor(ResourceProxy):
    def __init__(self, problem_id, source_code):
        super(ResourceProxy, self).__init__()
        source_code_file = problem_id + '.java'
        with open(source_code_file, 'wb') as fo:
            fo.write(source_code)
        output_file = problem_id + '.class'
        javac_args = [env['runtime']['javac'], source_code_file]
        javac_process = subprocess.Popen(javac_args, stderr=subprocess.PIPE)
        _, compile_error = javac_process.communicate()
        self._files = [source_code_file, output_file]
        self._class_name = problem_id
        if javac_process.returncode != 0:
            os.unlink(source_code_file)
            raise CompileError(compile_error)

    def launch(self, *args, **kwargs):
        return JavaPopen(['java', '-client',
                          '-Xmx%sK' % kwargs.get('memory'), '-jar', JAVA_EXECUTOR, os.getcwd(),
                          self._class_name, str(kwargs.get('time') * 1000)] + list(args),
                         executable=env['runtime']['java'])


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