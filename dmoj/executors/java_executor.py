import errno
import glob
import os
import re
import subprocess
import sys
from collections import deque
from pathlib import Path, PurePath
from typing import Any, Dict, List, Optional, Tuple, Type

from dmoj.cptbox import Debugger, TracedPopen
from dmoj.cptbox.filesystem_policies import ExactDir, ExactFile, FilesystemAccessRule, RecursiveDir
from dmoj.error import CompileError, InternalError
from dmoj.executors.compiled_executor import CompiledExecutor
from dmoj.executors.mixins import SingleDigitVersionMixin
from dmoj.judgeenv import skip_self_test
from dmoj.result import Result
from dmoj.utils.unicode import utf8bytes, utf8text

recomment = re.compile(r'/\*.*?\*/', re.DOTALL | re.U)
restring = re.compile(r''''(?:\\.|[^'\\])'|"(?:\\.|[^"\\])*"''', re.DOTALL | re.U)
reinline_comment = re.compile(r'//.*?(?=[\r\n])', re.U)
reclass = re.compile(
    r'\bpublic\s+(?:strictfp\s+)?(?:(?:abstract|final)\s+)?(?:strictfp\s+)?class\s+([\w$][\w$]*?)\b', re.U
)
repackage = re.compile(r'\bpackage\s+([^.;]+(?:\.[^.;]+)*?);', re.U)
reexception = re.compile(r'7257b50d-e37a-4664-b1a5-b1340b4206c0: (.*?)$', re.U | re.M)

JAVA_SANDBOX = os.path.abspath(os.path.join(os.path.dirname(__file__), 'java_sandbox.jar'))


def find_class(source: str) -> str:
    source = reinline_comment.sub('', restring.sub('', recomment.sub('', source)))
    class_name = reclass.search(source)
    if class_name is None:
        raise CompileError('No public class: your main class must be declared as a "public class"\n')
    package = repackage.search(source)
    if package:
        raise CompileError(f'Invalid package {package.group(1)}: do not declare package\n')
    return class_name.group(1)


def handle_procctl(debugger: Debugger) -> bool:
    P_PID = 0
    PROC_STACKGAP_CTL = 17
    PROC_STACKGAP_STATUS = 18
    return (
        debugger.arg0 == P_PID
        and debugger.arg1 == debugger.pid
        and debugger.arg2 in (PROC_STACKGAP_CTL, PROC_STACKGAP_STATUS)
    )


class JavaExecutor(SingleDigitVersionMixin, CompiledExecutor):
    ext = 'java'

    vm: str
    compiler: str
    nproc = -1
    fsize = 1048576  # Allow 1 MB for writing crash log.
    address_grace = 786432
    syscalls = [
        'pread64',
        'clock_nanosleep',
        'socketpair',
        ('procctl', handle_procctl),
        'setrlimit',
        'thr_set_name',
        'getcpu',
    ]

    jvm_regex: Optional[str] = None
    _class_name: Optional[str]

    def __init__(self, problem_id: str, source_code: bytes, **kwargs) -> None:
        self._class_name = None
        self._agent_file = JAVA_SANDBOX
        super().__init__(problem_id, source_code, **kwargs)

    def get_compile_popen_kwargs(self) -> Dict[str, Any]:
        return {'executable': utf8bytes(self.get_compiler())}

    def get_compiled_file(self) -> str:
        return ''

    def get_executable(self) -> str:
        vm = self.get_vm()
        assert vm is not None
        return vm

    def get_fs(self) -> List[FilesystemAccessRule]:
        fs = (
            super().get_fs()
            + [ExactFile(self._agent_file)]
            + [ExactDir(str(parent)) for parent in PurePath(self._agent_file).parents]
        )
        vm = self.get_vm()
        assert vm is not None
        vm_parent = Path(os.path.realpath(vm)).parent.parent
        vm_config = Path(glob.glob(f'{vm_parent}/**/jvm.cfg', recursive=True)[0])
        if vm_config.is_symlink():
            fs += [RecursiveDir(os.path.dirname(os.path.realpath(vm_config)))]
        return fs

    def get_write_fs(self) -> List[FilesystemAccessRule]:
        assert self._dir is not None
        return super().get_write_fs() + [ExactFile(os.path.join(self._dir, 'submission_jvm_crash.log'))]

    def get_agent_flag(self) -> str:
        hints = [*self._hints]
        if self.unbuffered:
            hints.append('nobuf')
        return f'-javaagent:{self._agent_file}={",".join(hints)}'

    def get_cmdline(self, **kwargs) -> List[str]:
        # 128m is equivalent to 1<<27 in Thread constructor
        return [
            'java',
            self.get_vm_mode(),
            self.get_agent_flag(),
            '-Xss128m',
            f'-Xmx{kwargs["orig_memory"]}K',
            '-XX:+UseSerialGC',
            '-XX:+DisplayVMOutputToStderr',  # print the failed VM initialization errors to stderr
            '-XX:ErrorFile=submission_jvm_crash.log',
            self._class_name or '',
        ]

    def launch(self, *args, **kwargs) -> TracedPopen:
        kwargs['orig_memory'], kwargs['memory'] = kwargs['memory'], 0
        return super().launch(*args, **kwargs)

    def populate_result(self, stderr: bytes, result: Result, process: TracedPopen) -> None:
        super().populate_result(stderr, result, process)
        if process.is_ir:
            failed_init_errors = [
                b'Too small maximum heap',
                b'Too small initial heap',
                b'GC triggered before VM initialization completed',
            ]
            if any(error in stderr for error in failed_init_errors) or result.feedback == 'java.lang.OutOfMemoryError':
                result.feedback = ''
                result.result_flag |= Result.MLE

    def parse_feedback_from_stderr(self, stderr: bytes, process: TracedPopen) -> str:
        if process.returncode:
            assert self._dir is not None
            try:
                with open(os.path.join(self._dir, 'submission_jvm_crash.log'), 'r') as err:
                    log = err.read()
                    # "Newer" (post-Java 8) JVMs regressed a bit in terms of handling out-of-memory situations during
                    # initialization, whereby they now dump a crash log rather than exiting with
                    # java.lang.OutOfMemoryError. Handle this case so that we don't erroneously emit internal errors.
                    if 'There is insufficient memory for the Java Runtime' in log:
                        return 'insufficient memory to initialize JVM'
                    else:
                        raise InternalError('\n\n' + log)
            except IOError:
                pass

        if b'Error: Main method not found in class' in stderr:
            exception = 'public static void main(String[] args) not found'
        else:
            match = deque(reexception.finditer(utf8text(stderr, 'replace')), maxlen=1)
            if not match:
                exception = 'abnormal termination'  # Probably exited without calling shutdown hooks
            else:
                exception = match[0].group(1).split(':')[0]

        return exception

    @classmethod
    def get_vm(cls) -> Optional[str]:
        return cls.runtime_dict.get(cls.vm)

    @classmethod
    def get_vm_mode(cls) -> str:
        return f'-{cls.runtime_dict.get(cls.vm + "_mode", "client")}'

    @classmethod
    def get_compiler(cls) -> Optional[str]:
        return cls.runtime_dict.get(cls.compiler)

    @classmethod
    def initialize(cls) -> bool:
        vm = cls.get_vm()
        compiler = cls.get_compiler()
        if vm is None or compiler is None:
            return False
        if not os.path.isfile(vm) or not os.path.isfile(compiler):
            return False
        return skip_self_test or cls.run_self_test()

    @classmethod
    def test_jvm(cls, name: str, path: str) -> Tuple[Dict[str, Any], bool, str]:
        raise NotImplementedError()

    @classmethod
    def get_versionable_commands(cls):
        return [('javac', cls.get_compiler())]

    @classmethod
    def get_version_flags(cls, command):
        return ['-version']

    @classmethod
    def autoconfig(cls) -> Tuple[Optional[Dict[str, Any]], bool, str, str]:
        if cls.jvm_regex is None:
            return {}, False, 'Unimplemented', ''

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
                    return {}, False, 'Unimplemented', ''
                else:
                    if success:
                        return config, success, message, ''
        return {}, False, 'Could not find JVM', ''

    @classmethod
    def unravel_java(cls, path: str) -> str:
        with open(path, 'rb') as f:
            if f.read(2) != '#!':
                return os.path.realpath(path)

        with open(os.devnull, 'w') as devnull:
            process = subprocess.Popen(['bash', '-x', path, '-version'], stdout=devnull, stderr=subprocess.PIPE)

        log = [i for i in process.communicate()[1].split(b'\n') if b'exec' in i]
        cmdline = log[-1].lstrip(b'+ ').split()
        return utf8text(cmdline[1]) if len(cmdline) > 1 else os.path.realpath(path)


class JavacExecutor(JavaExecutor):
    def create_files(self, problem_id: str, source_code: bytes, *args, **kwargs) -> None:
        super().create_files(problem_id, source_code, *args, **kwargs)
        # This step is necessary because of Unicode classnames
        try:
            source = utf8text(source_code)
        except UnicodeDecodeError:
            raise CompileError('Your UTF-8 is bad, and you should feel bad')
        class_name = find_class(source)
        self._code = self._file(f'{class_name}.java')
        try:
            with open(self._code, 'wb') as fo:
                fo.write(utf8bytes(source))
        except IOError as e:
            if e.errno in (errno.ENAMETOOLONG, errno.ENOENT, errno.EINVAL):
                raise CompileError('Why do you need a class name so long? As a judge, I sentence your code to death.\n')
            raise
        self._class_name = class_name

    def get_compile_args(self) -> List[str]:
        compiler = self.get_compiler()
        assert compiler is not None
        assert self._code is not None
        return [compiler, '-Xlint', '-encoding', 'UTF-8', self._code]

    def handle_compile_error(self, output: bytes):
        if b'is public, should be declared in a file named' in utf8bytes(output):
            raise CompileError('You are a troll. Trolls are not welcome. As a judge, I sentence your code to death.\n')
        raise CompileError(output)

    @classmethod
    def test_jvm(cls, name: str, path: str) -> Tuple[Dict[str, Any], bool, str]:
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

                executor: Type[JavacExecutor] = type('Executor', (cls,), {'runtime_dict': result})
                success = executor.run_self_test(output=False)
                if success:
                    # Don't pollute the YAML in the usual case where it's -client
                    if mode == 'client':
                        del result[cls_vm_mode]
                    return result, success, f'Using {vm_path} ({mode} VM)'
            else:
                # If absolutely no VM mode works, then we've failed the self test
                return result, False, 'Failed self-test'
        else:
            return {}, False, 'Invalid JDK'
