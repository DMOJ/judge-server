from __future__ import print_function

import hashlib
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import traceback
from distutils.spawn import find_executable
from subprocess import Popen

import pylru
import six

from dmoj.error import CompileError
from dmoj.executors.mixins import PlatformExecutorMixin
from dmoj.judgeenv import env
from dmoj.utils.ansi import ansi_style
from dmoj.utils.communicate import *
from dmoj.utils.error import print_protection_fault
from dmoj.utils.unicode import utf8bytes, utf8text
from dmoj.utils.uniprocess import Popen as UniPopen

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
    version_regex = re.compile('.*?(\d+(?:\.\d+)+)', re.DOTALL)

    def __init__(self, problem_id, source_code, dest_dir=None, hints=None,
                 unbuffered=False, **kwargs):
        self._tempdir = dest_dir or env.tempdir
        self._dir = None
        self.problem = problem_id
        self.source = source_code
        self._hints = hints or []
        self.unbuffered = unbuffered

    def cleanup(self):
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

    def _file(self, *paths):
        # Defer creation of temporary submission directory until first file is created,
        # because we may not need one (e.g. for cached executors).
        if self._dir is None:
            self._dir = tempfile.mkdtemp(dir=self._tempdir)
        return os.path.join(self._dir, *paths)

    @classmethod
    def get_executor_name(cls):
        return cls.__module__.split('.')[-1]

    def get_executable(self):
        return None

    def get_cmdline(self):
        raise NotImplementedError()

    def get_nproc(self):
        return self.nproc

    def launch_unsafe(self, *args, **kwargs):
        return Popen(self.get_cmdline() + list(args),
                     env=self.get_env(), executable=self.get_executable(),
                     cwd=self._dir, **kwargs)

    @classmethod
    def get_command(cls):
        return cls.runtime_dict.get(cls.command)

    @classmethod
    def initialize(cls, sandbox=True):
        if cls.get_command() is None:
            return False
        if not os.path.isfile(cls.get_command()):
            return False
        return cls.run_self_test(sandbox)

    @classmethod
    def run_self_test(cls, sandbox=True, output=True, error_callback=None):
        if not cls.test_program:
            return True

        if output:
            print(ansi_style("%-39s%s" % ('Self-testing #ansi[%s](|underline):' % cls.get_executor_name(), '')), end=' ')
        try:
            executor = cls(cls.test_name, utf8bytes(cls.test_program))
            proc = executor.launch(time=cls.test_time, memory=cls.test_memory) if sandbox else executor.launch_unsafe()
            test_message = b'echo: Hello, World!'
            stdout, stderr = proc.communicate(test_message + b'\n')

            if proc.tle:
                print(ansi_style('#ansi[Time Limit Exceeded](red|bold)'))
                return False
            if proc.mle:
                print(ansi_style('#ansi[Memory Limit Exceeded](red|bold)'))
                return False

            res = stdout.strip() == test_message and not stderr
            if output:
                # Cache the versions now, so that the handshake packet doesn't take ages to generate
                cls.get_runtime_versions()
                usage = '[%.3fs, %d KB]' % (proc.execution_time, proc.max_memory)
                print(ansi_style(['#ansi[Failed](red|bold)', '#ansi[Success](green|bold)'][res]), usage)
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
                print(ansi_style('#ansi[Failed](red|bold)'))
                traceback.print_exc()
            if error_callback:
                error_callback(traceback.format_exc())
            return False

    @classmethod
    def get_versionable_commands(cls):
        return ((cls.command, cls.get_command())),

    @classmethod
    def get_runtime_versions(cls):
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
    def parse_version(cls, command, output):
        match = cls.version_regex.match(output)
        if match:
            return map(int, match.group(1).split('.'))
        return None

    @classmethod
    def get_version_flags(cls, command):
        return ['--version']

    @classmethod
    def find_command_from_list(cls, files):
        for file in files:
            if os.path.isabs(file):
                if os.path.exists(file):
                    return file
            else:
                path = find_executable(file)
                if path is not None:
                    return os.path.abspath(path)

    @classmethod
    def autoconfig_find_first(cls, mapping):
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
    def autoconfig_run_test(cls, result):
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
    def get_find_first_mapping(cls):
        if cls.command is None:
            return None
        return {cls.command: cls.command_paths or [cls.command]}

    @classmethod
    def autoconfig(cls):
        return cls.autoconfig_find_first(cls.get_find_first_mapping())


class ScriptExecutor(BaseExecutor):
    def __init__(self, problem_id, source_code, **kwargs):
        super(ScriptExecutor, self).__init__(problem_id, source_code, **kwargs)
        self._code = self._file(problem_id + self.ext)
        self.create_files(problem_id, source_code)

    @classmethod
    def get_command(cls):
        if cls.command in cls.runtime_dict:
            return cls.runtime_dict[cls.command]
        name = cls.get_executor_name().lower()
        if '%s_home' % name in cls.runtime_dict:
            return os.path.join(cls.runtime_dict['%s_home' % name], 'bin', cls.command)

    def get_fs(self):
        home = self.runtime_dict.get('%s_home' % self.get_executor_name().lower())
        fs = super(ScriptExecutor, self).get_fs() + [self._code]
        if home is not None:
            fs.append(re.escape(home))
        return fs

    def create_files(self, problem_id, source_code):
        with open(self._code, 'wb') as fo:
            fo.write(utf8bytes(source_code))

    def get_cmdline(self):
        return [self.get_command(), self._code]

    def get_executable(self):
        return self.get_command()

    def get_env(self):
        env = super(BaseExecutor, self).get_env()
        env_key = self.get_executor_name().lower() + '_env'
        if env_key in self.runtime_dict:
            env = env or {}
            env.update(self.runtime_dict[env_key])
        return env


# A lot of executors must do initialization during their constructors, which is
# complicated by the CompiledExecutor compiling *during* its constructor. From a
# user's perspective, though, once an Executor is instantiated, it should be ready
# to launch (e.g. the user shouldn't have to care about compiling themselves). As
# a compromise, we use a metaclass to compile after all constructors have ran.
#
# Using a metaclass also allows us to handle caching executors transparently.
# Contract: if cached=True is specified and an entry exists in the cache,
# `create_files` and `compile` will not be run, and `_executable` will be loaded
# from the cache.
class CompiledExecutorMeta(type):
    def _cleanup_cache_entry(key, executor):
        # Mark the executor as not-cached, so that if this is the very last reference
        # to it, __del__ will clean it up.
        executor.is_cached = False

    compiled_binary_cache = pylru.lrucache(env.compiled_binary_cache_size, _cleanup_cache_entry)

    def __call__(self, *args, **kwargs):
        is_cached = kwargs.get('cached')
        if is_cached:
            kwargs['dest_dir'] = env.compiled_binary_cache_dir

        # Finish running all constructors before compiling.
        obj = super(CompiledExecutorMeta, self).__call__(*args, **kwargs)
        obj.is_cached = is_cached

        # Before writing sources to disk, check if we have this executor in our cache.
        if is_cached:
            cache_key = obj.__class__.__name__ + obj.__module__ + obj.get_binary_cache_key()
            cache_key = hashlib.sha384(utf8bytes(cache_key)).hexdigest()
            if cache_key in self.compiled_binary_cache:
                executor = self.compiled_binary_cache[cache_key]
                # Minimal sanity checking: is the file still there? If not, we'll just recompile.
                if os.path.isfile(executor._executable):
                    obj._executable = executor._executable
                    obj._dir = executor._dir
                    return obj

        obj.create_files(*args, **kwargs)
        obj.compile()

        if is_cached:
            self.compiled_binary_cache[cache_key] = obj

        return obj


class CompiledExecutor(six.with_metaclass(CompiledExecutorMeta, BaseExecutor)):
    executable_size = env.compiler_size_limit * 1024
    compiler_time_limit = env.compiler_time_limit
    compile_output_index = 1

    class TimedPopen(UniPopen):
        def __init__(self, *args, **kwargs):
            self._time = kwargs.pop('time_limit', None)
            super(CompiledExecutor.TimedPopen, self).__init__(*args, **kwargs)

            self._killed = False
            if self._time:
                # Spawn thread to kill process after it times out
                self._shocker = threading.Thread(target=self._shocker_thread)
                self._shocker.start()

        def _shocker_thread(self):
            # Though this shares a name with the shocker thread used for submissions, where the process shocker thread
            # is a fine scalpel that ends a TLE process with surgical precision, this is more like a rusty hatchet
            # that beheads a misbehaving compiler.
            #
            # It's not very accurate: time starts ticking in the next line, regardless of whether the process is
            # actually running, and the time is updated in 0.25s intervals. Nonetheless, it serves the purpose of
            # not allowing the judge to die.
            #
            # See <https://github.com/DMOJ/judge/issues/141>
            start_time = time.time()

            while self.returncode is None:
                if time.time() - start_time > self._time:
                    self._killed = True
                    try:
                        if os.name != 'nt':
                            os.killpg(self.pid, signal.SIGKILL)
                        else:
                            self.terminate()
                    except OSError:
                        # This can happen if the process exits quickly
                        pass
                    break
                time.sleep(0.25)

        def communicate(self, input=None):
            ret = super(CompiledExecutor.TimedPopen, self).communicate(input=input)
            if self._killed:
                return ret[0], 'compiler timed out (> %d seconds)\n%s' % (self._time, ret[1])
            return ret

    def __init__(self, problem_id, source_code, *args, **kwargs):
        super(CompiledExecutor, self).__init__(problem_id, source_code, **kwargs)
        self.warning = None
        self._executable = None

    def cleanup(self):
        if not self.is_cached:
            super(CompiledExecutor, self).cleanup()

    def create_files(self, problem_id, source_code, *args, **kwargs):
        self._code = self._file(problem_id + self.ext)
        with open(self._code, 'wb') as fo:
            fo.write(utf8bytes(source_code))

    def get_compile_args(self):
        raise NotImplementedError()

    def get_compile_env(self):
        return None

    def get_compile_popen_kwargs(self):
        return {}

    def create_executable_limits(self):
        try:
            import resource

            def limit_executable():
                os.setpgrp()
                resource.setrlimit(resource.RLIMIT_FSIZE, (self.executable_size, self.executable_size))

            return limit_executable
        except ImportError:
            return None

    def get_compile_process(self):
        kwargs = {'stderr': subprocess.PIPE, 'cwd': self._dir, 'env': self.get_compile_env(),
                  'preexec_fn': self.create_executable_limits(), 'time_limit': self.compiler_time_limit}
        kwargs.update(self.get_compile_popen_kwargs())

        return self.TimedPopen(self.get_compile_args(), **kwargs)

    def get_compile_output(self, process):
        # Use safe_communicate because otherwise, malicious submissions can cause a compiler
        # to output hundreds of megabytes of data as output before being killed by the time limit,
        # which effectively murders the MySQL database waiting on the site server.
        limit = env.compiler_output_character_limit
        return safe_communicate(process, None, outlimit=limit, errlimit=limit)[self.compile_output_index]

    def get_compiled_file(self):
        return self._file(self.problem)

    def is_failed_compile(self, process):
        return process.returncode != 0 or (hasattr(process, '_killed') and process._killed)

    def handle_compile_error(self, output):
        raise CompileError(output)

    def get_binary_cache_key(self):
        return self.problem + self.source

    def compile(self):
        process = self.get_compile_process()
        try:
            output = self.get_compile_output(process)
        except OutputLimitExceeded:
            output = 'compiler output too long (> 64kb)'

        if self.is_failed_compile(process):
            self.handle_compile_error(output)
        self.warning = output

        self._executable = self.get_compiled_file()
        return self._executable

    def get_cmdline(self):
        return [self.problem]

    def get_executable_ext(self):
        return ['', '.exe'][os.name == 'nt']

    def get_executable(self):
        return self._executable + self.get_executable_ext()


class ShellExecutor(ScriptExecutor):
    nproc = -1
    shell_commands = ['cat', 'grep', 'awk', 'perl']

    def get_shell_commands(self):
        return self.shell_commands

    def get_allowed_exec(self):
        return list(map(find_executable, self.get_shell_commands()))

    def get_fs(self):
        return super(ShellExecutor, self).get_fs() + self.get_allowed_exec()

    def get_allowed_syscalls(self):
        return super(ShellExecutor, self).get_allowed_syscalls() + [
            'fork', 'waitpid', 'wait4'
        ]

    def get_security(self, launch_kwargs=None):
        from dmoj.cptbox.syscalls import sys_execve, sys_access, sys_eaccess

        sec = super(ShellExecutor, self).get_security(launch_kwargs)
        allowed = set(self.get_allowed_exec())

        def handle_execve(debugger):
            path = sec.get_full_path(debugger, debugger.readstr(debugger.uarg0))
            if path in allowed:
                return True
            print('Not allowed to use command:', path, file=sys.stderr)
            return False

        sec[sys_execve] = handle_execve
        sec[sys_eaccess] = sec[sys_access]
        return sec

    def get_env(self):
        env = super(ShellExecutor, self).get_env()
        env['PATH'] = os.environ['PATH']
        return env
