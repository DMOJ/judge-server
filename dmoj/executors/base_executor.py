import errno
import os
import re
import shutil
import subprocess
import sys
import tempfile
import traceback
from distutils.spawn import find_executable
from typing import Callable, Dict, Iterable, List, Optional, Tuple, Union

from dmoj.executors.mixins import PlatformExecutorMixin
from dmoj.judgeenv import env
from dmoj.utils.ansi import print_ansi
from dmoj.utils.error import print_protection_fault
from dmoj.utils.unicode import utf8bytes, utf8text

version_cache = {}


class BaseExecutor(PlatformExecutorMixin):
    ext = None
    nproc = 0
    command = None
    command_paths = []
    runtime_dict = env.runtime
    name = '(unknown)'
    test_program = ''
    test_name = 'self_test'
    test_time = env.selftest_time_limit
    test_memory = env.selftest_memory_limit
    version_regex = re.compile(r'.*?(\d+(?:\.\d+)+)', re.DOTALL)
    source_filename_format = '{problem_id}.{ext}'

    def __init__(self, problem_id: str, source_code: bytes, dest_dir: Optional[str] = None,
                 hints: Optional[List[str]] = None, unbuffered: bool = False, **kwargs):
        self._tempdir = dest_dir or env.tempdir
        self._dir = None
        self.problem = problem_id
        self.source = source_code
        self._hints = hints or []
        self.unbuffered = unbuffered

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

    def __del__(self):
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

    def get_cmdline(self):
        raise NotImplementedError()

    def get_nproc(self) -> int:
        return self.nproc

    def launch_unsafe(self, *args: str, **kwargs) -> subprocess.Popen:
        return subprocess.Popen(self.get_cmdline() + list(args),
                                env=self.get_env(), executable=self.get_executable(),
                                cwd=self._dir, **kwargs)

    @classmethod
    def get_command(cls) -> Optional[str]:
        return cls.runtime_dict.get(cls.command)

    @classmethod
    def initialize(cls, sandbox=True) -> bool:
        if cls.get_command() is None:
            return False
        if not os.path.isfile(cls.get_command()):
            return False
        return cls.run_self_test(sandbox)

    @classmethod
    def run_self_test(cls, sandbox: bool = True, output: bool = True,
                      error_callback: Optional[Callable[[any], any]] = None) -> bool:
        if not cls.test_program:
            return True

        if output:
            print_ansi("%-39s%s" % ('Self-testing #ansi[%s](|underline):' % cls.get_executor_name(), ''), end=' ')
        try:
            executor = cls(cls.test_name, utf8bytes(cls.test_program))
            if sandbox:
                proc = executor.launch(time=cls.test_time, memory=cls.test_memory,
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            else:
                proc = executor.launch_unsafe()
            test_message = b'echo: Hello, World!'
            stdout, stderr = proc.communicate(test_message + b'\n')

            if proc.tle:
                print_ansi('#ansi[Time Limit Exceeded](red|bold)')
                return False
            if proc.mle:
                print_ansi('#ansi[Memory Limit Exceeded](red|bold)')
                return False

            res = stdout.strip() == test_message and not stderr
            if output:
                # Cache the versions now, so that the handshake packet doesn't take ages to generate
                cls.get_runtime_versions()
                usage = '[%.3fs, %d KB]' % (proc.execution_time, proc.max_memory)
                print_ansi(['#ansi[Failed](red|bold)', '#ansi[Success](green|bold)'][res], usage)
            if stdout.strip() != test_message and error_callback:
                error_callback('Got unexpected stdout output:\n' + utf8text(stdout))
            if stderr:
                if error_callback:
                    error_callback('Got unexpected stderr output:\n' + utf8text(stderr))
                else:
                    print(stderr, file=sys.stderr)
            if hasattr(proc, 'protection_fault') and proc.protection_fault:
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
    def get_versionable_commands(cls) -> Tuple[Tuple[str, str], ...]:
        return (cls.command, cls.get_command()),

    @classmethod
    def get_runtime_versions(cls) -> Tuple[Tuple[str, Optional[Tuple[int, ...]]], ...]:
        key = cls.get_executor_name()
        if key in version_cache:
            return version_cache[key]

        vers = []
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
                        version = tuple(version)
                        break
            vers.append((runtime, version or ()))

        version_cache[key] = tuple(vers)
        return version_cache[key]

    @classmethod
    def parse_version(cls, command: str, output: str) -> Optional[Iterable[int]]:
        match = cls.version_regex.match(output)
        if match:
            return map(int, match.group(1).split('.'))
        return None

    @classmethod
    def get_version_flags(cls, command: str) -> List[str]:
        return ['--version']

    @classmethod
    def find_command_from_list(cls, files: str) -> Optional[str]:
        for file in files:
            if os.path.isabs(file):
                if os.path.exists(file):
                    return file
            else:
                path = find_executable(file)
                if path is not None:
                    return os.path.abspath(path)
        return None

    @classmethod
    def autoconfig_find_first(cls, mapping) -> Tuple[dict, bool, str]:
        if mapping is None:
            return {}, False, 'Unimplemented'
        result = {}

        for key, files in mapping.items():
            file = cls.find_command_from_list(files)
            if file is None:
                return None, False, 'Failed to find "%s"' % key
            result[key] = file
        return cls.autoconfig_run_test(result)

    @classmethod
    def autoconfig_run_test(cls, result: dict) -> Tuple[dict, bool, str, str]:
        executor = type('Executor', (cls,), {'runtime_dict': result})
        executor.__module__ = cls.__module__
        errors = []
        success = executor.run_self_test(output=False, error_callback=errors.append)
        if success:
            message = ''
            if len(result) == 1:
                message = 'Using %s' % list(result.values())[0]
        else:
            message = 'Failed self-test'
        return result, success, message, '\n'.join(errors)

    @classmethod
    def get_find_first_mapping(cls) -> Optional[Dict[str, List[str]]]:
        if cls.command is None:
            return None
        return {cls.command: cls.command_paths or [cls.command]}

    @classmethod
    def autoconfig(cls) -> Tuple[dict, bool, str]:
        return cls.autoconfig_find_first(cls.get_find_first_mapping())


class ScriptExecutor(BaseExecutor):
    def __init__(self, problem_id: str, source_code: bytes, **kwargs):
        super(ScriptExecutor, self).__init__(problem_id, source_code, **kwargs)
        self._code = self._file(
            self.source_filename_format.format(problem_id=problem_id, ext=self.ext))
        self.create_files(problem_id, source_code)

    @classmethod
    def get_command(cls) -> str:
        if cls.command in cls.runtime_dict:
            return cls.runtime_dict[cls.command]
        name = cls.get_executor_name().lower()
        if '%s_home' % name in cls.runtime_dict:
            return os.path.join(cls.runtime_dict['%s_home' % name], 'bin', cls.command)

    def get_fs(self) -> List[str]:
        home = self.runtime_dict.get('%s_home' % self.get_executor_name().lower())
        fs = super(ScriptExecutor, self).get_fs() + [self._code]
        if home is not None:
            fs.append(re.escape(home))
        return fs

    def create_files(self, problem_id: str, source_code: bytes) -> None:
        with open(self._code, 'wb') as fo:
            fo.write(utf8bytes(source_code))

    def get_cmdline(self) -> List[str]:
        return [self.get_command(), self._code]

    def get_executable(self) -> str:
        return self.get_command()

    def get_env(self) -> dict:
        env = super(BaseExecutor, self).get_env()
        env_key = self.get_executor_name().lower() + '_env'
        if env_key in self.runtime_dict:
            env = env or {}
            env.update(self.runtime_dict[env_key])
        return env
