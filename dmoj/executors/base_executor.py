import errno
import os
import re
import shutil
import subprocess
import sys
import tempfile
import traceback
from distutils.spawn import find_executable
from typing import Any, Callable, Dict, List, Optional, Tuple

from dmoj.executors.mixins import PlatformExecutorMixin
from dmoj.judgeenv import env
from dmoj.utils.ansi import print_ansi
from dmoj.utils.error import print_protection_fault
from dmoj.utils.unicode import utf8bytes, utf8text

version_cache: Dict[str, List[Tuple[str, Optional[Tuple[int, ...]]]]] = {}


class BaseExecutor(PlatformExecutorMixin):
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

    _dir: Optional[str] = None

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
        return cls.run_self_test()

    @classmethod
    def run_self_test(cls, output: bool = True,
                      error_callback: Optional[Callable[[Any], Any]] = None) -> bool:
        if not cls.test_program:
            return True

        if output:
            print_ansi("%-39s%s" % ('Self-testing #ansi[%s](|underline):' % cls.get_executor_name(), ''), end=' ')
        try:
            executor = cls(cls.test_name, utf8bytes(cls.test_program))
            proc = executor.launch(time=cls.test_time, memory=cls.test_memory,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE)

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
                print_ansi("%s %-19s" % (['#ansi[Failed](red|bold) ',
                                          '#ansi[Success](green|bold)'][res], usage), end=' ')

                runtime_version: List[Tuple[str, str]] = []
                for runtime, version in cls.get_runtime_versions():
                    assert version is not None
                    runtime_version.append((runtime, '.'.join(map(str, version))))

                print_ansi(', '.join(["#ansi[%s](cyan|bold) %s" % v for v in runtime_version]))
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
    def get_runtime_versions(cls) -> List[Tuple[str, Optional[Tuple[int, ...]]]]:
        key = cls.get_executor_name()
        if key in version_cache:
            return version_cache[key]

        versions: List[Tuple[str, Optional[Tuple[int, ...]]]] = []
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
    def autoconfig_find_first(cls, mapping) -> Tuple[Optional[dict], bool, str, str]:
        if mapping is None:
            return {}, False, 'Unimplemented', ''
        result = {}

        for key, files in mapping.items():
            file = cls.find_command_from_list(files)
            if file is None:
                return None, False, 'Failed to find "%s"' % key, ''
            result[key] = file
        return cls.autoconfig_run_test(result)

    @classmethod
    def autoconfig_run_test(cls, result: dict) -> Tuple[dict, bool, str, str]:
        executor: Any = type('Executor', (cls,), {'runtime_dict': result})
        executor.__module__ = cls.__module__
        errors: List[str] = []
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
    def autoconfig(cls) -> Tuple[Optional[dict], bool, str, str]:
        return cls.autoconfig_find_first(cls.get_find_first_mapping())
