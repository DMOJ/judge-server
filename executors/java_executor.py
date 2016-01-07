import os
import re
import sys
import time
import errno
from subprocess import Popen, PIPE

from communicate import safe_communicate, OutputLimitExceeded
from error import CompileError
from .resource_proxy import ResourceProxy

try:
    from winutils import max_memory, execution_time
except ImportError:
    windows = False
    max_memory, execution_time = None, None
else:
    windows = True

recomment = re.compile(r'/\*.*?\*/', re.DOTALL)
restring = re.compile(r''''(?:\\.|[^'\\])'|"(?:\\.|[^"\\])*"''', re.DOTALL)
reinline_comment = re.compile(r'//.*?(?=[\r\n])')
reclass = re.compile(r'\bpublic\s+class\s+([_a-zA-Z\$][_0-9a-zA-z\$]*?)\b')
repackage = re.compile(r'\bpackage\s+([^.;]+(?:\.[^.;]+)*?);')
redeunicode = re.compile(r'\\u([0-9a-f]{4})', re.I)
deunicode = lambda x: redeunicode.sub(lambda a: unichr(int(a.group(1), 16)), x)
JAVA_EXECUTOR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'java_executor.jar'))


def find_class(source):
    source = reinline_comment.sub('', restring.sub('', recomment.sub('', source)))
    class_name = reclass.search(source)
    if class_name is None:
        raise CompileError('No public class: your main class must be declared as a "public class"')
    package = repackage.search(source)
    if package:
        raise CompileError('Invalid package %s: do not declare package' % package.group(1))
    return class_name


class JavaProcess(object):
    def __init__(self, java, class_name, cwd, time_limit, memory_limit, statefile, vm='client'):
        self.process = self.spawn_process(class_name, cwd, java, memory_limit, time_limit, vm)
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
        self._start = time.time()

    def spawn_process(self, class_name, cwd, java, memory_limit, time_limit, vm):
        return Popen(self.get_command_line(class_name, cwd, memory_limit, time_limit, vm),
                     executable=java, cwd=cwd, stdin=PIPE, stdout=PIPE, stderr=PIPE,
                     env=self.get_environ(class_name, cwd, java, memory_limit, time_limit, vm))

    def get_command_line(self, class_name, cwd, memory_limit, time_limit, vm):
        return ['java', '-%s' % vm, '-Xmx%sK' % memory_limit, '-jar', JAVA_EXECUTOR, cwd,
                class_name, str(int(time_limit * 1000)), 'state']

    def get_environ(self, class_name, cwd, java, memory_limit, time_limit, vm):
        return None

    def communicate(self, stdin=None):
        output = self.process.communicate(stdin)
        self._update_stats()
        return output

    def _update_windows_stats(self):
        handle = int(self.process._handle)
        self.execution_time = execution_time(handle)
        self.tie = self.execution_time > self.time_limit
        self.max_memory = max_memory(handle) / 1024.
        self.mle = self.max_memory > self.memory_limit
        if self.returncode is None:
            self.returncode = self.process.returncode

    def _fallback_unix_stats(self):
        self.execution_time = time.time() - self._start
        self.tle = self.execution_time > self.time_limit
        self.max_memory = 0
        self.mle = 0
        self.returncode = -1

    def safe_communicate(self, stdin=None, outlimit=None, errlimit=None):
        try:
            output = safe_communicate(self.process, stdin, outlimit, errlimit)
        except OutputLimitExceeded:
            if windows:
                self._update_windows_stats()
            else:
                self._fallback_unix_stats()
            raise
        else:
            self._update_stats()
            return output

    def _update_stats(self):
        try:
            with open(self.statefile, 'r') as proc:
                self.error_info = proc.read().strip()
        except Exception:
            return
        try:
            data = self.error_info.split(None, 5)
            self.execution_time, self.tle, self.max_memory, self.mle, self.returncode = map(int, data[:5])
            self.feedback = data[5]
        except Exception:
            if not windows:
                print>> sys.stderr, self.error_info
                self._fallback_unix_stats()
                return
        if windows:
            self._update_windows_stats()
        else:
            self.execution_time /= 1000000000.0
        if self.returncode == -1:
            self.returncode = 1
        if self.feedback == 'OK':
            self.feedback = None

    def kill(self):
        self._killed = True
        return self.process.kill()

    def wait(self):
        self.process.wait()
        self._update_stats()
        return self.returncode

    def poll(self):
        if self.returncode is None:
            if self.process.poll() is None:
                return None
            self._update_stats()
        return self.returncode

    @property
    def r_execution_time(self):
        return self.execution_time

    def __getattr__(self, attr):
        return getattr(self.process, attr)


class JavaExecutor(ResourceProxy):
    ext = '.java'
    name = 'JAVA'

    vm = None
    compiler = None
    process_class = JavaProcess

    test_program = ''
    test_name = 'self_test'
    test_time = 1
    test_memory = 65536

    def __init__(self, problem_id, source_code):
        super(JavaExecutor, self).__init__()
        self.statefile = self._file('state')
        self._class_name = None
        self.warning = None
        self.create_files(problem_id, source_code)
        self.compile()

    def create_files(self, problem_id, source_code):
        self._code = self._file(problem_id + self.ext)
        with open(self._code, 'wb') as fo:
            fo.write(source_code)

    def get_compile_args(self):
        raise NotImplementedError()

    def get_compile_env(self):
        return None

    def get_compile_popen_kwargs(self):
        return {}

    def get_compile_process(self):
        kwargs = {'stderr': PIPE, 'cwd': self._dir, 'env': self.get_compile_env()}
        kwargs.update(self.get_compile_popen_kwargs())
        return Popen(self.get_compile_args(), **kwargs)

    def get_compile_output(self, process):
        return process.communicate()[1]

    def is_failed_compile(self, process):
        return process.returncode != 0

    def handle_compile_error(self, output):
        raise CompileError(output)

    def compile(self):
        process = self.get_compile_process()
        output = self.get_compile_output(process)

        if self.is_failed_compile(process):
            self.handle_compile_error(output)
        self.warning = output

    def launch(self, *args, **kwargs):
        return self.process_class(java=self.get_vm(), class_name=self._class_name, cwd=self._dir,
                                  time_limit=kwargs.get('time'), memory_limit=kwargs.get('memory'),
                                  statefile=self.statefile)

    def launch_unsafe(self, *args, **kwargs):
        return Popen(['java', '-client', self._class_name] + list(args),
                     executable=self.get_vm(), cwd=self._dir, **kwargs)

    @classmethod
    def get_vm(cls):
        return cls.vm

    @classmethod
    def get_compiler(cls):
        return cls.compiler

    @classmethod
    def initialize(cls, sandbox=True):
        if cls.get_vm() is None or cls.get_compiler() is None:
            return False
        if not os.path.isfile(cls.get_vm()) or not os.path.isfile(cls.get_compiler()):
            return False
        if not cls.test_program:
            return True

        print 'Self-testing: %s executor:' % cls.name,
        try:
            executor = cls(cls.test_name, cls.test_program)
            proc = executor.launch(time=cls.test_time, memory=cls.test_memory) \
                if sandbox else executor.launch_unsafe()
            test_message = 'echo: Hello, World!'
            stdout, stderr = proc.communicate(test_message)
            res = stdout.strip() == test_message and not stderr
            print ['Failed', 'Success'][res]
            if stderr:
                print>> sys.stderr, stderr
            return res
        except Exception:
            print 'Failed'
            import traceback
            traceback.print_exc()
            return False


class JavacExecutor(JavaExecutor):
    def create_files(self, problem_id, source_code):
        source_code = deunicode(source_code)
        class_name = find_class(source_code)
        self._code = self._file('%s.java' % class_name.group(1))
        try:
            with open(self._code, 'wb') as fo:
                fo.write(source_code)
        except IOError as e:
            if e.errno in (errno.ENAMETOOLONG, errno.ENOENT):
                raise CompileError('Why do you need a class name so long? '
                                   'As a judge, I sentence your code to death.')
            raise
        self._class_name = class_name.group(1)

    def get_compile_args(self):
        return [self.get_compiler(), self._code]

    def handle_compile_error(self, output):
        if 'is public, should be declared in a file named' in output:
            raise CompileError('You are a troll. Trolls are not welcome. '
                               'As a judge, I sentence your code to death.')
        raise CompileError(output)
