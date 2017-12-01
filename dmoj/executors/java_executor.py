import errno
import subprocess
import sys
import os
import re
from shutil import copyfile
from subprocess import Popen

import six

from dmoj.error import CompileError, InternalError
from dmoj.utils.unicode import utf8bytes, utf8text
from .base_executor import CompiledExecutor
from dmoj.result import Result

recomment = re.compile(br'/\*.*?\*/', re.DOTALL)
restring = re.compile(br''''(?:\\.|[^'\\])'|"(?:\\.|[^"\\])*"''', re.DOTALL)
reinline_comment = re.compile(br'//.*?(?=[\r\n])')
reclass = re.compile(br'\bpublic\s+(?:strictfp\s+)?(?:(?:abstract|final)\s+)?(?:strictfp\s+)?class\s+([_a-zA-Z\$][_0-9a-zA-z\$]*?)\b')
repackage = re.compile(br'\bpackage\s+([^.;]+(?:\.[^.;]+)*?);')
redeunicode = re.compile(br'\\u([0-9a-f]{4})', re.I)
deunicode = lambda x: redeunicode.sub(lambda a: six.unichr(int(a.group(1), 16)), x)


JAVA_SANDBOX = os.path.abspath(os.path.join(os.path.dirname(__file__), 'java-sandbox.jar'))

POLICY_PREFIX = '''\
grant codeBase "file:///{agent}" {{
    permission java.io.FilePermission "state", "write";
}};

'''

with open(os.path.join(os.path.dirname(__file__), 'java-security.policy')) as policy_file:
    policy = policy_file.read()


def find_class(source):
    source = reinline_comment.sub(b'', restring.sub(b'', recomment.sub(b'', source)))
    class_name = reclass.search(source)
    if class_name is None:
        raise CompileError('No public class: your main class must be declared as a "public class"\n')
    package = repackage.search(source)
    if package:
        raise CompileError('Invalid package %s: do not declare package\n' % utf8text(package.group(1), 'replace'))
    return class_name


class JavaExecutor(CompiledExecutor):
    ext = '.java'

    vm = None
    compiler = None
    nproc = -1
    address_grace = 786432

    jvm_regex = None
    security_policy = policy

    def __init__(self, problem_id, source_code, **kwargs):
        self._class_name = None
        super(JavaExecutor, self).__init__(problem_id, source_code, **kwargs)

    def create_files(self, problem_id, source_code, *args, **kwargs):
        super(JavaExecutor, self).create_files(problem_id, source_code, *args, **kwargs)

        if os.name == 'nt':
            self._agent_file = self._file('java-sandbox.jar')
            copyfile(JAVA_SANDBOX, self._agent_file)
        else:
            self._agent_file = JAVA_SANDBOX

        self._policy_file = self._file('security.policy')
        with open(self._policy_file, 'w') as file:
            # Normalize path separators because the security policy is processed by a StringTokenizer which treats
            # escapes sequences as... escape sequences.
            path = self._agent_file.replace('\\', '/') if os.name == 'nt' else self._agent_file
            file.write(POLICY_PREFIX.format(agent=path) + self.security_policy)

    def get_compile_popen_kwargs(self):
        return {'executable': self.get_compiler()}

    def get_compiled_file(self):
        return None

    def get_security(self, launch_kwargs=None):
        return None

    def get_executable(self):
        return self.get_vm()

    def get_cmdline(self):
        agent_flags = '-javaagent:%s=policy:%s' % (self._agent_file, self._policy_file)
        for hint in self._hints:
            agent_flags += ',%s' % hint
        # 128m is equivalent to 1<<27 in Thread constructor
        return ['java', '-client', agent_flags, '-Xss128m', '-Xmx%dK' % self.__memory_limit,
                '-XX:+UseSerialGC', '-XX:ErrorFile=submission_jvm_crash.log', self._class_name]

    def launch(self, *args, **kwargs):
        self.__memory_limit = kwargs['memory']
        kwargs['memory'] = 0
        return super(JavaExecutor, self).launch(*args, **kwargs)

    def launch_unsafe(self, *args, **kwargs):
        return Popen(['java', '-client', self._class_name] + list(args),
                     executable=self.get_vm(), cwd=self._dir, **kwargs)

    def get_feedback(self, stderr, result, process):
        if process.returncode:
            try:
                with open(os.path.join(self._dir, 'submission_jvm_crash.log'), 'r') as err:
                    raise InternalError('\n\n' + err.read())
            except IOError:
                pass
        if not result.result_flag & Result.IR:
            return ''

        try:
            with open(os.path.join(self._dir, 'state'), 'r') as state:
                exception = state.read().strip()
        except IOError:
            exception = "abnormal termination"  # Probably exited without calling shutdown hooks

        return exception

    @classmethod
    def get_vm(cls):
        return cls.runtime_dict.get(cls.vm)

    @classmethod
    def get_compiler(cls):
        return cls.runtime_dict.get(cls.compiler)

    @classmethod
    def initialize(cls, sandbox=True):
        if cls.get_vm() is None or cls.get_compiler() is None:
            return False
        if not os.path.isfile(cls.get_vm()) or not os.path.isfile(cls.get_compiler()):
            return False
        return cls.run_self_test(sandbox)

    @classmethod
    def test_jvm(cls, name, path):
        raise NotImplementedError()

    @classmethod
    def get_versionable_commands(cls):
        return [('javac', cls.get_compiler())]

    @classmethod
    def get_version_flags(cls, command):
        return ['-version']

    @classmethod
    def autoconfig(cls):
        if cls.jvm_regex is None:
            return {}, False, 'Unimplemented'

        JVM_DIR = '/usr/local' if sys.platform.startswith('freebsd') else '/usr/lib/jvm'
        regex = re.compile(cls.jvm_regex)

        try:
            vms = os.listdir(JVM_DIR)
        except OSError:
            vms = []

        for item in vms:
            path = os.path.join(JVM_DIR, item)
            if not os.path.isdir(path) or os.path.islink(path):
                continue

            if regex.match(item):
                try:
                    config, success, message = cls.test_jvm(item, path)
                except (NotImplementedError, TypeError, ValueError):
                    return {}, False, 'Unimplemented'
                else:
                    if success:
                        return config, success, message
        return {}, False, 'Could not find JVM'

    @classmethod
    def unravel_java(cls, path):
        with open(path, 'rb') as f:
            if f.read(2) != '#!':
                return path

        with open(os.devnull, 'w') as devnull:
            process = subprocess.Popen(['bash', '-x', path, '-version'], stdout=devnull, stderr=subprocess.PIPE)

        log = [i for i in process.communicate()[1].split('\n') if 'exec' in i]
        cmdline = log[-1].lstrip('+ ').split()
        return cmdline[1] if len(cmdline) > 1 else path


class JavacExecutor(JavaExecutor):
    def create_files(self, problem_id, source_code, *args, **kwargs):
        super(JavacExecutor, self).create_files(problem_id, source_code, *args, **kwargs)
        source_code = deunicode(source_code)
        class_name = find_class(source_code)
        self._code = self._file('%s.java' % utf8text(class_name.group(1)))
        try:
            with open(self._code, 'wb') as fo:
                fo.write(utf8bytes(source_code))
        except IOError as e:
            if e.errno in (errno.ENAMETOOLONG, errno.ENOENT):
                raise CompileError('Why do you need a class name so long? '
                                   'As a judge, I sentence your code to death.\n')
            raise
        self._class_name = class_name.group(1)

    def get_compile_args(self):
        return [self.get_compiler(), '-Xlint', '-encoding', 'UTF-8', self._code]

    def handle_compile_error(self, output):
        if b'is public, should be declared in a file named' in output:
            raise CompileError('You are a troll. Trolls are not welcome. '
                               'As a judge, I sentence your code to death.\n')
        raise CompileError(output)

    @classmethod
    def test_jvm(cls, name, path):
        vm_path = os.path.join(path, 'bin', 'java')
        compiler_path = os.path.join(path, 'bin', 'javac')
        result = {cls.vm: vm_path, cls.compiler: compiler_path}

        if os.path.isfile(vm_path) and os.path.isfile(compiler_path):
            executor = type('Executor', (cls,), {'runtime_dict': result})
            success = executor.run_self_test(output=False)
            return result, success, 'Using %s' % vm_path if success else 'Failed self-test'
        else:
            return result, False, 'Invalid JDK'
