import os
import threading
import subprocess
import sys
import traceback
from distutils.spawn import find_executable
from shutil import copyfile
from subprocess import Popen

import time

from dmoj.error import CompileError
from dmoj.executors.resource_proxy import ResourceProxy
from dmoj.judgeenv import env
from dmoj.utils.ansi import ansi_style

try:
    from dmoj.cptbox import SecurePopen, PIPE, CHROOTSecurity, syscalls
    from dmoj.cptbox.handlers import ALLOW
except ImportError:
    SecurePopen, PIPE, CHROOTSecurity, ALLOW, syscalls = None, None, None, None, None
    from dmoj.wbox import WBoxPopen, default_inject32, default_inject64, default_inject_func
else:
    WBoxPopen = default_inject32 = default_inject64 = default_inject_func = None

BASE_FILESYSTEM = ['.*\.so', '/dev/(?:null|zero|full|random|urandom|stdin|stdout|stderr|tty)$',
                   '/proc/self/maps$', '/proc/self$', '/proc/(?:meminfo|stat|cpuinfo$)',
                   '/usr/', '/sys/devices/system/cpu/online$', '/etc/(?:localtime$)', '/$']

if 'freebsd' in sys.platform:
    BASE_FILESYSTEM += ['/etc/spwd.db$']

class BaseExecutor(ResourceProxy):
    ext = None
    network_block = True
    address_grace = 65536
    nproc = 0
    fs = ['.*\.so']
    syscalls = []
    command = None
    command_paths = []
    runtime_dict = env['runtime']
    name = '(unknown)'
    inject32 = env.get('inject32', default_inject32)
    inject64 = env.get('inject64', default_inject64)
    inject_func = env.get('inject_func', default_inject_func)
    test_program = ''
    test_name = 'self_test'
    test_time = 10
    test_memory = 65536
    wbox_popen_class = WBoxPopen
    cptbox_popen_class = SecurePopen

    def __init__(self, problem_id, source_code, **kwargs):
        super(BaseExecutor, self).__init__()
        self.problem = problem_id
        self.source = source_code

    def get_fs(self):
        name = self.__class__.__module__.split('.')[-1]
        return BASE_FILESYSTEM + self.fs + env.get('extra_fs', {}).get(name, [])

    def get_allowed_syscalls(self):
        return self.syscalls

    def get_security(self, launch_kwargs=None):
        if CHROOTSecurity is None:
            raise NotImplementedError('No security manager on Windows')
        sec = CHROOTSecurity(self.get_fs(), io_redirects=launch_kwargs.get('io_redirects', None))
        for name in self.get_allowed_syscalls():
            if isinstance(name, tuple) and len(name) == 2:
                name, handler = name
            else:
                handler = ALLOW
            sec[getattr(syscalls, 'sys_' + name)] = handler
        return sec

    def get_executable(self):
        return None

    def get_cmdline(self):
        raise NotImplementedError()

    def get_env(self):
        if WBoxPopen is not None:
            return None
        return {'LANG': 'C'}

    def get_network_block(self):
        assert WBoxPopen is not None
        return self.network_block

    def get_address_grace(self):
        assert SecurePopen is not None
        return self.address_grace

    def get_nproc(self):
        return self.nproc

    def get_inject32(self):
        file = self._file('dmsec32.dll')
        copyfile(self.inject32, file)
        return file

    def get_inject64(self):
        file = self._file('dmsec64.dll')
        copyfile(self.inject64, file)
        return file

    def get_inject_func(self):
        return self.inject_func

    if SecurePopen is None:
        def launch(self, *args, **kwargs):
            return self.wbox_popen_class(self.get_cmdline() + list(args),
                                         time=kwargs.get('time'), memory=kwargs.get('memory'),
                                         cwd=self._dir, executable=self.get_executable(),
                                         network_block=True, env=self.get_env(),
                                         nproc=self.get_nproc() + 1,
                                         inject32=self.get_inject32(),
                                         inject64=self.get_inject64(),
                                         inject_func=self.get_inject_func())
    else:
        def launch(self, *args, **kwargs):
            return self.cptbox_popen_class(self.get_cmdline() + list(args), executable=self.get_executable(),
                                           security=self.get_security(launch_kwargs=kwargs),
                                           address_grace=self.get_address_grace(),
                                           time=kwargs.get('time'), memory=kwargs.get('memory'),
                                           stderr=(PIPE if kwargs.get('pipe_stderr', False) else None),
                                           env=self.get_env(), cwd=self._dir, nproc=self.get_nproc(),
                                           unbuffered=kwargs.get('unbuffered', False))

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
            print ansi_style("%-39s%s" % ('Self-testing #ansi[%s](|underline):' % cls.name, '')),
        try:
            executor = cls(cls.test_name, cls.test_program)
            proc = executor.launch(time=cls.test_time, memory=cls.test_memory) if sandbox else executor.launch_unsafe()
            test_message = 'echo: Hello, World!'
            stdout, stderr = proc.communicate(test_message + '\n')
            res = stdout.strip() == test_message and not stderr
            if output:
                print ansi_style(['#ansi[Failed](red|bold)', '#ansi[Success](green|bold)'][res])
            if stderr:
                if error_callback:
                    error_callback('Got unexpected stderr output:\n' + stderr)
                else:
                    print>> sys.stderr, stderr
            return res
        except Exception:
            if output:
                print ansi_style('#ansi[Failed](red|bold)')
                traceback.print_exc()
            if error_callback:
                error_callback(traceback.format_exc())
            return False

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

        for key, files in mapping.iteritems():
            file = cls.find_command_from_list(files)
            if file is None:
                return result, False, 'Failed to find "%s"' % key
            result[key] = file

        return cls.autoconfig_run_test(result)

    @classmethod
    def autoconfig_run_test(cls, result):
        executor = type('Executor', (cls,), {'runtime_dict': result})
        errors = []
        success = executor.run_self_test(output=False, error_callback=errors.append)
        if success:
            message = ''
            if len(result) == 1:
                message = 'Using %s' % result.values()[0]
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

    def create_files(self, problem_id, source_code):
        with open(self._code, 'wb') as fo:
            fo.write(source_code)

    def get_cmdline(self):
        return [self.get_command(), self._code]

    def get_executable(self):
        return self.get_command()


class CompiledExecutor(BaseExecutor):
    executable_size = 131072 * 1024  # 128mb
    compiler_time_limit = 10

    class TimedPopen(subprocess.Popen):
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
                    try:
                        # Give the process a bit of time to clean up after itself
                        self.terminate()
                        if os.name != 'nt':
                            time.sleep(0.5)
                            self.kill()  # On Windows this is an alias for terminate()
                    except OSError:
                        # This can happen if the process exits quickly
                        pass
                    self._killed = True
                    break
                time.sleep(0.25)

        def communicate(self, input=None):
            ret = super(CompiledExecutor.TimedPopen, self).communicate(input=input)
            if self._killed:
                return ret[0], 'compiler timed out (> %d seconds)\n%s' % (self._time, ret[1])
            return ret

    def __init__(self, problem_id, source_code, *args, **kwargs):
        super(CompiledExecutor, self).__init__(problem_id, source_code, **kwargs)
        self.create_files(problem_id, source_code, *args, **kwargs)
        self.warning = None
        self._executable = self.compile()

    def create_files(self, problem_id, source_code, *args, **kwargs):
        self._code = self._file(problem_id + self.ext)
        with open(self._code, 'wb') as fo:
            fo.write(source_code)

    def get_compile_args(self):
        raise NotImplementedError()

    def get_compile_env(self):
        return None

    def get_compile_popen_kwargs(self):
        return {}

    def create_executable_fslimit(self):
        try:
            import resource

            def limit_executable_size():
                resource.setrlimit(resource.RLIMIT_FSIZE, (self.executable_size, self.executable_size))

            return limit_executable_size
        except ImportError:
            return None

    def get_compile_process(self):
        kwargs = {'stderr': subprocess.PIPE, 'cwd': self._dir, 'env': self.get_compile_env(),
                  'preexec_fn': self.create_executable_fslimit(), 'time_limit': self.compiler_time_limit}
        kwargs.update(self.get_compile_popen_kwargs())

        return self.TimedPopen(self.get_compile_args(), **kwargs)

    def get_compile_output(self, process):
        return process.communicate()[1]

    def get_compiled_file(self):
        return self._file(self.problem)

    def is_failed_compile(self, process):
        return process.returncode != 0 or (hasattr(process, '_killed') and process._killed)

    def handle_compile_error(self, output):
        raise CompileError(output)

    def compile(self):
        process = self.get_compile_process()
        output = self.get_compile_output(process)

        if self.is_failed_compile(process):
            self.handle_compile_error(output)
        self.warning = output
        return self.get_compiled_file()

    def get_cmdline(self):
        return [self.problem]

    def get_executable_ext(self):
        return ['', '.exe'][os.name == 'nt']

    def get_executable(self):
        return self._executable + self.get_executable_ext()
