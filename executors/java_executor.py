import errno
import os
import re
from shutil import copyfile
from subprocess import Popen

from error import CompileError
from .base_executor import CompiledExecutor

from result import Result
from collections import deque

recomment = re.compile(r'/\*.*?\*/', re.DOTALL)
restring = re.compile(r''''(?:\\.|[^'\\])'|"(?:\\.|[^"\\])*"''', re.DOTALL)
reinline_comment = re.compile(r'//.*?(?=[\r\n])')
reclass = re.compile(r'\bpublic\s+class\s+([_a-zA-Z\$][_0-9a-zA-z\$]*?)\b')
repackage = re.compile(r'\bpackage\s+([^.;]+(?:\.[^.;]+)*?);')
redeunicode = re.compile(r'\\u([0-9a-f]{4})', re.I)
reexception = re.compile('^d4519cd6-6270-4bbb-a040-9bf4bcbd5938:(.*?)$', re.MULTILINE)
deunicode = lambda x: redeunicode.sub(lambda a: unichr(int(a.group(1), 16)), x)

JAVA_SANDBOX = os.path.abspath(os.path.join(os.path.dirname(__file__), 'java-sandbox.jar'))
with open(os.path.join(os.path.dirname(__file__), 'java-security.policy')) as policy_file:
    policy = policy_file.read()


def find_class(source):
    source = reinline_comment.sub('', restring.sub('', recomment.sub('', source)))
    class_name = reclass.search(source)
    if class_name is None:
        raise CompileError('No public class: your main class must be declared as a "public class"')
    package = repackage.search(source)
    if package:
        raise CompileError('Invalid package %s: do not declare package' % package.group(1))
    return class_name


class JavaExecutor(CompiledExecutor):
    ext = '.java'
    name = 'JAVA'

    vm = None
    compiler = None
    nproc = -1

    def __init__(self, problem_id, source_code):
        self._class_name = None
        super(JavaExecutor, self).__init__(problem_id, source_code)

    def create_files(self, problem_id, source_code, *args, **kwargs):
        super(JavaExecutor, self).create_files(problem_id, source_code, *args, **kwargs)
        self._policy_file = self._file('security.policy')
        with open(self._policy_file, 'w') as file:
            file.write(policy)

        if os.name == 'nt':
            self._agent_file = self._file('java-sandbox.jar')
            copyfile(JAVA_SANDBOX, self._agent_file)
        else:
            self._agent_file = JAVA_SANDBOX

    def get_compile_popen_kwargs(self):
        return {'executable': self.get_compiler()}

    def get_compiled_file(self):
        return None

    def get_security(self):
        return None

    def get_executable(self):
        return self.get_vm()

    def get_cmdline(self):
        return ['java', '-client', '-javaagent:%s=policy:%s' % (self._agent_file, self._policy_file),
                '-Xss128m', '-Xmx%dK' % self.__memory_limit, self._class_name] # 128m is equivalent to 1<<27 in Thread constructor

    def launch(self, *args, **kwargs):
        self.__memory_limit = kwargs['memory']
        kwargs['memory'] = 0
        return super(JavaExecutor, self).launch(*args, **kwargs)

    def launch_unsafe(self, *args, **kwargs):
        return Popen(['java', '-client', self._class_name] + list(args),
                     executable=self.get_vm(), cwd=self._dir, **kwargs)
                     
    def get_feedback(self, stderr, result):
        if not result.result_flag & Result.IR or not stderr or len(stderr) > 2048:
            return ''
        match = deque(reexception.finditer(stderr), maxlen=1)
        if not match:
            return ''
        exception = match[0].group(1).strip()
        return exception

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
        return cls.run_self_test(sandbox)


class JavacExecutor(JavaExecutor):
    def create_files(self, problem_id, source_code, *args, **kwargs):
        super(JavacExecutor, self).create_files(problem_id, source_code, *args, **kwargs)
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
