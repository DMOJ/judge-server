import errno
import os
import re
import shutil
import subprocess
import sys
import tempfile
import traceback
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

from dmoj.cptbox import IsolateTracer, TracedPopen, syscalls
from dmoj.cptbox.filesystem_policies import ExactDir, ExactFile, FilesystemAccessRule, RecursiveDir
from dmoj.cptbox.handlers import ALLOW
from dmoj.error import InternalError
from dmoj.judgeenv import env, skip_self_test
from dmoj.result import Result
from dmoj.utils import setbufsize_path
from dmoj.utils.ansi import print_ansi
from dmoj.utils.error import print_protection_fault
from dmoj.utils.unicode import utf8bytes, utf8text

version_cache: Dict[str, List[Tuple[str, Tuple[int, ...]]]] = {}

if os.path.isdir('/usr/home'):
    USR_DIR = [RecursiveDir(f'/usr/{d}') for d in os.listdir('/usr') if d != 'home' and os.path.isdir(f'/usr/{d}')]
else:
    USR_DIR = [RecursiveDir('/usr')]

BASE_FILESYSTEM: List[FilesystemAccessRule] = [
    ExactFile('/dev/null'),
    ExactFile('/dev/tty'),
    ExactFile('/dev/zero'),
    ExactFile('/dev/urandom'),
    ExactFile('/dev/random'),
    *USR_DIR,
    RecursiveDir('/lib'),
    RecursiveDir('/lib32'),
    RecursiveDir('/lib64'),
    RecursiveDir('/opt'),
    ExactDir('/etc'),
    ExactFile('/etc/localtime'),
    ExactFile('/etc/timezone'),
    ExactDir('/usr'),
    ExactDir('/tmp'),
    ExactDir('/'),
]

BASE_WRITE_FILESYSTEM: List[FilesystemAccessRule] = [ExactFile('/dev/null')]

if 'freebsd' in sys.platform:
    BASE_FILESYSTEM += [
        ExactFile('/etc/spwd.db'),
        ExactFile('/etc/pwd.db'),
        ExactFile('/dev/hv_tsc'),
        RecursiveDir('/dev/fd'),
    ]
else:
    BASE_FILESYSTEM += [
        ExactDir('/sys/devices/system/cpu'),
        ExactFile('/sys/devices/system/cpu/online'),
        ExactFile('/etc/selinux/config'),
    ]

if sys.platform.startswith('freebsd'):
    BASE_FILESYSTEM += [ExactFile('/etc/libmap.conf'), ExactFile('/var/run/ld-elf.so.hints')]
else:
    # Linux and kFreeBSD mounts linux-style procfs.
    BASE_FILESYSTEM += [
        ExactDir('/proc'),
        ExactDir('/proc/self'),
        ExactFile('/proc/self/maps'),
        ExactFile('/proc/self/exe'),
        ExactFile('/proc/self/auxv'),
        ExactFile('/proc/meminfo'),
        ExactFile('/proc/stat'),
        ExactFile('/proc/cpuinfo'),
        ExactFile('/proc/filesystems'),
        ExactDir('/proc/xen'),
        ExactFile('/proc/uptime'),
        ExactFile('/proc/sys/vm/overcommit_memory'),
    ]

    # Linux-style ld.
    BASE_FILESYSTEM += [ExactFile('/etc/ld.so.nohwcap'), ExactFile('/etc/ld.so.preload'), ExactFile('/etc/ld.so.cache')]

UTF8_LOCALE = 'C.UTF-8'

if sys.platform.startswith('freebsd') and sys.platform < 'freebsd13':
    UTF8_LOCALE = 'en_US.UTF-8'


class ExecutorMeta(type):
    def __new__(mcs, name, bases, attrs) -> Any:
        if '__module__' in attrs:
            attrs['name'] = attrs['__module__'].split('.')[-1]
        return super().__new__(mcs, name, bases, attrs)


class BaseExecutor(metaclass=ExecutorMeta):
    ext: str
    nproc = 0
    command: Optional[str] = None
    command_paths: List[str] = []
    runtime_dict = env.runtime
    name: str
    test_program: str
    test_name = 'self_test'
    test_time = env.selftest_time_limit
    test_memory = env.selftest_memory_limit
    version_regex = re.compile(r'.*?(\d+(?:\.\d+)+)', re.DOTALL)
    source_filename_format = '{problem_id}.{ext}'

    address_grace = 65536
    data_grace = 0
    fsize = 0
    personality = 0x0040000  # ADDR_NO_RANDOMIZE
    fs: List[FilesystemAccessRule] = []
    write_fs: List[FilesystemAccessRule] = []
    syscalls: List[Union[str, Tuple[str, Any]]] = []

    _dir: Optional[str] = None

    def __init__(
        self,
        problem_id: str,
        source_code: bytes,
        dest_dir: Optional[str] = None,
        hints: Optional[List[str]] = None,
        unbuffered: bool = False,
        **kwargs,
    ) -> None:
        self._tempdir = dest_dir or env.tempdir
        self._dir = None
        self.problem = problem_id
        self.source = source_code
        self._hints = hints or []
        self.unbuffered = unbuffered

        for arg, value in kwargs.items():
            if not hasattr(self, arg):
                raise TypeError(f'Unexpected keyword argument: {arg}')
            setattr(self, arg, value)

    def cleanup(self) -> None:
        if not hasattr(self, '_dir'):
            # We are really toasted, as constructor failed.
            print('BaseExecutor error: not initialized?')
            return

        # _dir may be None if an exception (e.g. CompileError) was raised during
        # create_files, e.g. by executors that perform source validation like
        # Java or Go.
        if self._dir:
            try:
                shutil.rmtree(self._dir)  # delete directory
            except OSError as exc:
                if exc.errno != errno.ENOENT:
                    raise

    def __del__(self) -> None:
        self.cleanup()

    def _file(self, *paths: str) -> str:
        # Defer creation of temporary submission directory until first file is created,
        # because we may not need one (e.g. for cached executors).
        if self._dir is None:
            self._dir = tempfile.mkdtemp(dir=self._tempdir)
        return os.path.join(self._dir, *paths)

    @classmethod
    def get_executor_name(cls) -> str:
        return cls.__module__.split('.')[-1]

    def get_executable(self) -> Optional[str]:
        return None

    def get_cmdline(self, **kwargs):
        raise NotImplementedError()

    def get_nproc(self) -> int:
        return self.nproc

    def populate_result(self, stderr: bytes, result: Result, process: TracedPopen) -> None:
        # Translate status codes/process results into Result object for status codes
        result.max_memory = process.max_memory or 0
        result.execution_time = process.execution_time or 0.0
        result.wall_clock_time = process.wall_clock_time or 0.0
        result.context_switches = process.context_switches or (0, 0)
        result.runtime_version = ', '.join(
            f'{runtime} {".".join(map(str, version))}' for runtime, version in self.get_runtime_versions()
        )

        if process.is_ir:
            result.result_flag |= Result.IR
        if process.is_rte:
            result.result_flag |= Result.RTE
        if process.is_ole:
            result.result_flag |= Result.OLE
        if process.is_tle:
            result.result_flag |= Result.TLE
        if process.is_mle:
            result.result_flag |= Result.MLE

        result.update_feedback(stderr, process, self)

    def parse_feedback_from_stderr(self, stderr: bytes, process: TracedPopen) -> str:
        return ''

    def _add_syscalls(self, sec: IsolateTracer, handlers: List[Union[str, Tuple[str, Any]]]) -> IsolateTracer:
        for item in handlers:
            if isinstance(item, tuple):
                name, handler = item
            else:
                name = item
                handler = ALLOW
            sec[getattr(syscalls, f'sys_{name}')] = handler
        return sec

    def get_security(self, launch_kwargs=None) -> IsolateTracer:
        sec = IsolateTracer(read_fs=self.get_fs(), write_fs=self.get_write_fs())
        return self._add_syscalls(sec, self.get_allowed_syscalls())

    def get_fs(self) -> List[FilesystemAccessRule]:
        assert self._dir is not None
        return BASE_FILESYSTEM + self.fs + self._load_extra_fs() + [RecursiveDir(self._dir)]

    def _load_extra_fs(self) -> List[FilesystemAccessRule]:
        name = self.get_executor_name()
        extra_fs_config = env.get('extra_fs', {}).get(name, [])
        extra_fs = []
        constructors: Dict[str, Type[FilesystemAccessRule]] = dict(
            exact_file=ExactFile, exact_dir=ExactDir, recursive_dir=RecursiveDir
        )
        for rules in extra_fs_config:
            for type, path in rules.iteritems():
                constructor = constructors.get(type)
                assert constructor, f"Can't load rule for extra path with rule type {type}"
                extra_fs.append(constructor(path))

        return extra_fs

    def get_write_fs(self) -> List[FilesystemAccessRule]:
        return BASE_WRITE_FILESYSTEM + self.write_fs

    def get_allowed_syscalls(self) -> List[Union[str, Tuple[str, Any]]]:
        return self.syscalls

    def get_address_grace(self) -> int:
        return self.address_grace

    def get_env(self) -> Dict[str, str]:
        env = {'LANG': UTF8_LOCALE}
        if self.unbuffered:
            env['CPTBOX_STDOUT_BUFFER_SIZE'] = '0'
        return env

    def launch(self, *args, **kwargs) -> TracedPopen:
        assert self._dir is not None
        for src, dst in kwargs.get('symlinks', {}).items():
            src = os.path.abspath(os.path.join(self._dir, src))
            # Disallow the creation of symlinks outside the submission directory.
            if os.path.commonprefix([src, self._dir]) == self._dir:
                # If a link already exists under this name, it's probably from a
                # previous case, but might point to something different.
                if os.path.islink(src):
                    os.unlink(src)
                os.symlink(dst, src)
            else:
                raise InternalError('cannot symlink outside of submission directory')

        agent = self._file('setbufsize.so')
        shutil.copyfile(setbufsize_path, agent)
        child_env = {
            # Forward LD_LIBRARY_PATH for systems (e.g. Android Termux) that require
            # it to find shared libraries
            'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
            'LD_PRELOAD': agent,
            'CPTBOX_STDOUT_BUFFER_SIZE': kwargs.get('stdout_buffer_size'),
            'CPTBOX_STDERR_BUFFER_SIZE': kwargs.get('stderr_buffer_size'),
        }
        child_env.update(self.get_env())

        executable = self.get_executable()
        assert executable is not None
        return TracedPopen(
            [utf8bytes(a) for a in self.get_cmdline(**kwargs) + list(args)],
            executable=utf8bytes(executable),
            security=self.get_security(launch_kwargs=kwargs),
            address_grace=self.get_address_grace(),
            data_grace=self.data_grace,
            personality=self.personality,
            time=kwargs.get('time', 0),
            memory=kwargs.get('memory', 0),
            wall_time=kwargs.get('wall_time'),
            stdin=kwargs.get('stdin'),
            stdout=kwargs.get('stdout'),
            stderr=kwargs.get('stderr'),
            env=child_env,
            cwd=utf8bytes(self._dir),
            nproc=self.get_nproc(),
            fsize=self.fsize,
            cpu_affinity=env.submission_cpu_affinity,
        )

    @classmethod
    def get_command(cls) -> Optional[str]:
        return cls.runtime_dict.get(cls.command)

    @classmethod
    def initialize(cls) -> bool:
        command = cls.get_command()
        if command is None:
            return False
        if not os.path.isfile(command):
            return False
        return skip_self_test or cls.run_self_test()

    @classmethod
    def run_self_test(cls, output: bool = True, error_callback: Optional[Callable[[Any], Any]] = None) -> bool:
        if not cls.test_program:
            return True

        if output:
            print_ansi(f'Self-testing #ansi[{cls.get_executor_name()}](|underline):'.ljust(39), end=' ')
        try:
            executor = cls(cls.test_name, utf8bytes(cls.test_program))
            proc = executor.launch(
                time=cls.test_time, memory=cls.test_memory, stdin=subprocess.PIPE, stdout=subprocess.PIPE
            )

            test_message = b'echo: Hello, World!'
            stdout, stderr = proc.communicate(test_message + b'\n')

            if proc.is_tle:
                print_ansi('#ansi[Time Limit Exceeded](red|bold)')
                return False
            if proc.is_mle:
                print_ansi('#ansi[Memory Limit Exceeded](red|bold)')
                return False

            res = stdout.strip() == test_message and not stderr
            if output:
                # Cache the versions now, so that the handshake packet doesn't take ages to generate
                cls.get_runtime_versions()
                usage = f'[{proc.execution_time:.3f}s, {proc.max_memory} KB]'
                print_ansi(f'{["#ansi[Failed](red|bold) ", "#ansi[Success](green|bold)"][res]} {usage:<19}', end=' ')
                print_ansi(
                    ', '.join(
                        [
                            f'#ansi[{runtime}](cyan|bold) {".".join(map(str, version))}'
                            for runtime, version in cls.get_runtime_versions()
                        ]
                    )
                )
            if stdout.strip() != test_message and error_callback:
                error_callback('Got unexpected stdout output:\n' + utf8text(stdout))
            if stderr:
                if error_callback:
                    error_callback('Got unexpected stderr output:\n' + utf8text(stderr))
                else:
                    print(stderr, file=sys.stderr)
            if proc.protection_fault:
                print_protection_fault(proc.protection_fault)
            return res
        except Exception:
            if output:
                print_ansi('#ansi[Failed](red|bold)')
                traceback.print_exc()
            if error_callback:
                error_callback(traceback.format_exc())
            return False

    @classmethod
    def get_versionable_commands(cls) -> List[Tuple[str, str]]:
        command = cls.get_command()
        assert cls.command is not None
        assert command is not None
        return [(cls.command, command)]

    @classmethod
    def get_runtime_versions(cls) -> List[Tuple[str, Tuple[int, ...]]]:
        key = cls.get_executor_name()
        if key in version_cache:
            return version_cache[key]

        versions: List[Tuple[str, Tuple[int, ...]]] = []
        for runtime, path in cls.get_versionable_commands():
            flags = cls.get_version_flags(runtime)

            version = None
            for flag in flags:
                try:
                    command = [path]
                    if isinstance(flag, (tuple, list)):
                        command.extend(flag)
                    else:
                        command.append(flag)
                    output = utf8text(subprocess.check_output(command, stderr=subprocess.STDOUT))
                except subprocess.CalledProcessError:
                    pass
                else:
                    version = cls.parse_version(runtime, output)
                    if version:
                        break
            versions.append((runtime, version or ()))

        version_cache[key] = versions
        return version_cache[key]

    @classmethod
    def parse_version(cls, command: str, output: str) -> Optional[Tuple[int, ...]]:
        match = cls.version_regex.match(output)
        if match:
            return tuple(map(int, match.group(1).split('.')))
        return None

    @classmethod
    def get_version_flags(cls, command: str) -> List[str]:
        return ['--version']

    @classmethod
    def find_command_from_list(cls, files: List[str]) -> Optional[str]:
        for file in files:
            if os.path.isabs(file):
                if os.path.exists(file):
                    return file
            else:
                path = shutil.which(file)
                if path is not None:
                    return os.path.abspath(path)
        return None

    @classmethod
    def autoconfig_find_first(
        cls, mapping: Optional[Dict[str, List[str]]]
    ) -> Tuple[Optional[Dict[str, Any]], bool, str, str]:
        if mapping is None:
            return {}, False, 'Unimplemented', ''
        result = {}

        for key, files in mapping.items():
            file = cls.find_command_from_list(files)
            if file is None:
                return None, False, f'Failed to find "{key}"', ''
            result[key] = file
        return cls.autoconfig_run_test(result)

    @classmethod
    def autoconfig_run_test(cls, result: Dict[str, Any]) -> Tuple[Dict[str, str], bool, str, str]:
        executor: Any = type('Executor', (cls,), {'runtime_dict': result})
        executor.__module__ = cls.__module__
        errors: List[str] = []
        success = executor.run_self_test(output=False, error_callback=errors.append)
        if success:
            message = ''
            if len(result) == 1:
                message = f'Using {list(result.values())[0]}'
        else:
            message = 'Failed self-test'
        return result, success, message, '\n'.join(errors)

    @classmethod
    def get_find_first_mapping(cls) -> Optional[Dict[str, List[str]]]:
        if cls.command is None:
            return None
        return {cls.command: cls.command_paths or [cls.command]}

    @classmethod
    def autoconfig(cls) -> Tuple[Optional[Dict[str, Any]], bool, str, str]:
        return cls.autoconfig_find_first(cls.get_find_first_mapping())
