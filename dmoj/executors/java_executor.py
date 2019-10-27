import errno
import os
import re
import subprocess
import sys
from collections import deque
from subprocess import Popen
from typing import Optional

from dmoj.error import CompileError, InternalError
from dmoj.executors.compiled_executor import CompiledExecutor
from dmoj.result import Result
from dmoj.utils.unicode import utf8bytes, utf8text

recomment = re.compile(r'/\*.*?\*/', re.DOTALL | re.U)
restring = re.compile(r''''(?:\\.|[^'\\])'|"(?:\\.|[^"\\])*"''', re.DOTALL | re.U)
reinline_comment = re.compile(r'//.*?(?=[\r\n])', re.U)
reclass = re.compile(r'\bpublic\s+(?:strictfp\s+)?(?:(?:abstract|final)\s+)?(?:strictfp\s+)?class\s+([\w\$][\w\$]*?)\b',
                     re.U)
repackage = re.compile(r'\bpackage\s+([^.;]+(?:\.[^.;]+)*?);', re.U)
reexception = re.compile(r'7257b50d-e37a-4664-b1a5-b1340b4206c0: (.*?)$', re.U | re.M)

JAVA_SANDBOX = os.path.abspath(os.path.join(os.path.dirname(__file__), 'java_sandbox.jar'))

with open(os.path.join(os.path.dirname(__file__), 'java-security.policy'), 'r') as policy_file:
    policy = policy_file.read()


def find_class(source):
    source = reinline_comment.sub('', restring.sub('', recomment.sub('', source)))
    class_name = reclass.search(source)
    if class_name is None:
        raise CompileError('No public class: your main class must be declared as a "public class"\n')
    package = repackage.search(source)
    if package:
        raise CompileError('Invalid package %s: do not declare package\n' % package.group(1))
    return class_name


class JavaExecutor(CompiledExecutor):
    ext = 'java'

    vm: str
    compiler: str
    nproc = -1
    fsize = 64  # Allow 64 bytes for dumping state file.
    address_grace = 786432

    jvm_regex: Optional[str] = None
    security_policy = policy

    def __init__(self, problem_id, source_code, **kwargs):
        self._class_name = None
        super().__init__(problem_id, source_code, **kwargs)

    def create_files(self, problem_id, source_code, *args, **kwargs):
        super().create_files(problem_id, source_code, *args, **kwargs)

        self._agent_file = JAVA_SANDBOX
        self._policy_file = self._file('security.policy')
        with open(self._policy_file, 'w') as file:
            file.write(self.security_policy)

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
        if self.unbuffered:
            agent_flags += ',nobuf'
        # 128m is equivalent to 1<<27 in Thread constructor
        return ['java', self.get_vm_mode(), agent_flags, '-Xss128m', '-Xmx%dK' % self.__memory_limit,
                '-XX:+UseSerialGC', '-XX:ErrorFile=submission_jvm_crash.log', self._class_name]

    def launch(self, *args, **kwargs):
        self.__memory_limit = kwargs['memory']
        kwargs['memory'] = 0
        return super().launch(*args, **kwargs)

    def launch_unsafe(self, *args, **kwargs):
        return Popen(['java', self.get_vm_mode(), self._class_name] + list(args),
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

        if b'Error: Main method not found in class' in stderr:
            exception = "public static void main(String[] args) not found"
        else:
            match = deque(reexception.finditer(utf8text(stderr, 'replace')), maxlen=1)
            if not match:
                exception = "abnormal termination"  # Probably exited without calling shutdown hooks
            else:
                exception = match[0].group(1)

        return exception

    @classmethod
    def get_vm(cls):
        return cls.runtime_dict.get(cls.vm)

    @classmethod
    def get_vm_mode(cls):
        return '-%s' % cls.runtime_dict.get(cls.vm + '_mode', 'client')

    @classmethod
    def get_compiler(cls):
        return cls.runtime_dict.get(cls.compiler)

    @classmethod
    def initialize(cls):
        if cls.get_vm() is None or cls.get_compiler() is None:
            return False
        if not os.path.isfile(cls.get_vm()) or not os.path.isfile(cls.get_compiler()):
            return False
        return cls.run_self_test()

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
        super().create_files(problem_id, source_code, *args, **kwargs)
        # This step is necessary because of Unicode classnames
        try:
            source_code = utf8text(source_code)
        except UnicodeDecodeError:
            raise CompileError('Your UTF-8 is bad, and you should feel bad')
        class_name = find_class(source_code)
        self._code = self._file('%s.java' % class_name.group(1))
        try:
            with open(self._code, 'wb') as fo:
                fo.write(utf8bytes(source_code))
        except IOError as e:
            if e.errno in (errno.ENAMETOOLONG, errno.ENOENT, errno.EINVAL):
                raise CompileError('Why do you need a class name so long? '
                                   'As a judge, I sentence your code to death.\n')
            raise
        self._class_name = class_name.group(1)

    def get_compile_args(self):
        return [self.get_compiler(), '-Xlint', '-encoding', 'UTF-8', self._code]

    def handle_compile_error(self, output):
        if b'is public, should be declared in a file named' in utf8bytes(output):
            raise CompileError('You are a troll. Trolls are not welcome. '
                               'As a judge, I sentence your code to death.\n')
        raise CompileError(output)

    @classmethod
    def test_jvm(cls, name, path):
        vm_path = os.path.join(path, 'bin', 'java')
        compiler_path = os.path.join(path, 'bin', 'javac')

        if os.path.isfile(vm_path) and os.path.isfile(compiler_path):
            # Not all JVMs have the same VMs available; specifically,
            # OpenJDK for ARM has no client VM, but has dcevm+server. So, we test
            # a bunch and if it's not the default (-client), then we list it
            # in the config.
            vm_modes = ['client', 'server', 'dcevm', 'zero']
            cls_vm_mode = cls.vm + '_mode'
            for mode in vm_modes:
                result = {cls.vm: vm_path, cls_vm_mode: mode, cls.compiler: compiler_path}

                executor = type('Executor', (cls,), {'runtime_dict': result})
                success = executor.run_self_test(output=False)
                if success:
                    # Don't pollute the YAML in the usual case where it's -client
                    if mode == 'client':
                        del result[cls_vm_mode]
                    return result, success, 'Using %s (%s VM)' % (vm_path, mode)
            else:
                # If absolutely no VM mode works, then we've failed the self test
                return result, False, 'Failed self-test'
        else:
            return {}, False, 'Invalid JDK'
