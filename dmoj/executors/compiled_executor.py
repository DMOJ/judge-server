import hashlib
import os
import signal
import subprocess
import threading
import time

import pylru

from dmoj.error import CompileError
from dmoj.judgeenv import env
from dmoj.utils.communicate import OutputLimitExceeded, safe_communicate
from dmoj.utils.unicode import utf8bytes
from .base_executor import BaseExecutor


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
class _CompiledExecutorMeta(type):
    @staticmethod
    def _cleanup_cache_entry(_key, executor: object) -> None:
        # Mark the executor as not-cached, so that if this is the very last reference
        # to it, __del__ will clean it up.
        executor.is_cached = False

    compiled_binary_cache = pylru.lrucache(env.compiled_binary_cache_size, _cleanup_cache_entry)

    def __call__(self, *args, **kwargs) -> object:
        is_cached = kwargs.get('cached')
        if is_cached:
            kwargs['dest_dir'] = env.compiled_binary_cache_dir

        # Finish running all constructors before compiling.
        obj = super(_CompiledExecutorMeta, self).__call__(*args, **kwargs)
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


class TimedPopen(subprocess.Popen):
    def __init__(self, *args, **kwargs):
        self._time = kwargs.pop('time_limit', None)
        super(TimedPopen, self).__init__(*args, **kwargs)

        self.timed_out = False
        if self._time:
            # Spawn thread to kill process after it times out
            self._shocker = threading.Thread(target=self._shocker_thread)
            self._shocker.start()

    def _shocker_thread(self) -> None:
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
                self.timed_out = True
                try:
                    os.killpg(self.pid, signal.SIGKILL)
                except OSError:
                    # This can happen if the process exits quickly
                    pass
                break
            time.sleep(0.25)


class CompiledExecutor(BaseExecutor, metaclass=_CompiledExecutorMeta):
    executable_size = env.compiler_size_limit * 1024
    compiler_time_limit = env.compiler_time_limit
    compile_output_index = 1

    def __init__(self, problem_id: str, source_code: str, *args, **kwargs):
        super(CompiledExecutor, self).__init__(problem_id, source_code, **kwargs)
        self.warning = None
        self._executable = None

    def cleanup(self) -> None:
        if not self.is_cached:
            super(CompiledExecutor, self).cleanup()

    def create_files(self, problem_id, source_code, *args, **kwargs) -> None:
        self._code = self._file(self.source_filename_format.format(problem_id=problem_id, ext=self.ext))
        with open(self._code, 'wb') as fo:
            fo.write(utf8bytes(source_code))

    def get_compile_args(self) -> None:
        raise NotImplementedError()

    def get_compile_env(self) -> None:
        return None

    def get_compile_popen_kwargs(self) -> dict:
        return {}

    def create_executable_limits(self) -> None:
        try:
            import resource

            def limit_executable():
                os.setpgrp()
                resource.setrlimit(resource.RLIMIT_FSIZE, (self.executable_size, self.executable_size))

            return limit_executable
        except ImportError:
            return None

    def get_compile_process(self) -> TimedPopen:
        kwargs = {'stderr': subprocess.PIPE, 'cwd': self._dir, 'env': self.get_compile_env(),
                  'preexec_fn': self.create_executable_limits(), 'time_limit': self.compiler_time_limit}
        kwargs.update(self.get_compile_popen_kwargs())

        return TimedPopen(self.get_compile_args(), **kwargs)

    def get_compile_output(self, process) -> Tuple[str, str]:
        # Use safe_communicate because otherwise, malicious submissions can cause a compiler
        # to output hundreds of megabytes of data as output before being killed by the time limit,
        # which effectively murders the MySQL database waiting on the site server.
        limit = env.compiler_output_character_limit
        return safe_communicate(process, None, outlimit=limit, errlimit=limit)[self.compile_output_index]

    def get_compiled_file(self) -> str:
        return self._file(self.problem)

    def is_failed_compile(self, process: TimedPopen) -> bool:
        return process.returncode != 0

    def handle_compile_error(self, output) -> None:
        raise CompileError(output)

    def get_binary_cache_key(self) -> str:
        return self.problem + self.source

    def compile(self) -> str:
        process = self.get_compile_process()
        try:
            output = self.get_compile_output(process)
        except OutputLimitExceeded:
            output = b'compiler output too long (> 64kb)'

        if self.is_failed_compile(process):
            if process.timed_out:
                output = b'compiler timed out (> %d seconds)' % self.compiler_time_limit
            self.handle_compile_error(output)
        self.warning = output

        self._executable = self.get_compiled_file()
        return self._executable

    def get_cmdline(self) -> List[str]:
        return [self.problem]

    def get_executable(self) -> str:
        return self._executable
