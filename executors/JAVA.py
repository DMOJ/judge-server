import os
import subprocess
from cptbox import SecurePopen, NullSecurity
from error import CompileError
from executors.utils import test_executor

from .resource_proxy import ResourceProxy
from judgeenv import env


class JavaPopen(object):
    def __init__(self, args, executable):
        self.process = subprocess.Popen(args, executable=executable,
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.execution_time, self.tle = None, None
        self.max_memory, self.mle = None, None
        self.stderr = None

    def communicate(self, stdin):
        stdout, stderr = self.process.communicate()
        self.execution_time, self.tle, self.max_memory, self.mle = map(int, stderr.split())
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
        return JavaPopen(['java', '-Djava.security.manager', '-Djava.security.policy=java_executor.policy', '-client',
                            '-Xmx%sK' % kwargs.get('memory'), '-cp', 'java_executor', 'JavaSafeExecutor', os.getcwd(),
                            self._class_name, kwargs.get('time') * 1000] + list(args),
                         executable=env['runtime']['java'])


def initialize():
    if 'java' not in env['runtime']:
        return False
    if not os.path.isfile(env['runtime']['java']):
        return False
    return test_executor('JAVA', Executor, r'''\
public class self_test {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
''', problem='self_test')