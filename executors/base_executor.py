import os
from subprocess import Popen
import subprocess
import sys
from error import CompileError

from .resource_proxy import ResourceProxy


try:
    from cptbox import SecurePopen, PIPE, CHROOTSecurity
except ImportError:
    SecurePopen, PIPE, CHROOTSecurity = None, None, None
    from wbox import WBoxPopen
else:
    WBoxPopen = None


class BaseExecutor(ResourceProxy):
    ext = None
    network_block = True
    address_grace = 4096
    nproc = 0
    fs = ['.*\.so']
    command = None
    name = '(unknown)'
    test_program = ''
    test_time = 1
    test_memory = 65536

    def __init__(self, problem_id, source_code):
        super(BaseExecutor, self).__init__()
        self.problem = problem_id
        self.source = source_code

    def get_fs(self):
        return self.fs

    def get_security(self):
        if CHROOTSecurity is None:
            raise NotImplementedError('No security manager on Windows')
        return CHROOTSecurity(self.get_fs())

    def get_executable(self):
        return None

    def get_cmdline(self):
        return [self.get_command(), self._code]

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

    if SecurePopen is None:
        def launch(self, *args, **kwargs):
            return WBoxPopen(self.get_cmdline() + list(args),
                             time=kwargs.get('time'), memory=kwargs.get('memory'),
                             cwd=self._dir, executable=self.get_executable(),
                             network_block=True, env=self.get_env(),
                             nproc=self.get_nproc() + 1)
    else:
        def launch(self, *args, **kwargs):
            return SecurePopen(self.get_cmdline() + list(args), executable=self.get_executable(),
                               security=self.get_security(), address_grace=self.get_address_grace(),
                               time=kwargs.get('time'), memory=kwargs.get('memory'),
                               stderr=(PIPE if kwargs.get('pipe_stderr', False) else None),
                               env=self.get_env(), cwd=self._dir, nproc=self.get_nproc())

    def launch_unsafe(self, *args, **kwargs):
        return Popen(self.get_cmdline() + list(args),
                     env=self.get_env(), executable=self.get_executable(),
                     cwd=self._dir, **kwargs)

    @classmethod
    def get_command(cls):
        return cls.command

    @classmethod
    def initialize(cls):
        if cls.get_command() is None:
            return False
        if not os.path.isfile(cls.get_command()):
            return False
        if not cls.test_program:
            return True

        print 'Self-testing: %s executor:' % cls.name,
        try:
            executor = cls('self_test', cls.test_program)
            proc = executor.launch(time=cls.test_time, memory=cls.test_memory)
            test_message = 'echo: Hello, World!'
            stdout, stderr = proc.communicate(test_message)
            res = stdout.strip() == test_message and not stderr
            print ['Failed', 'Success'][res]
            if stderr:
                print>>sys.stderr, stderr
            return res
        except Exception:
            print 'Failed'
            import traceback
            traceback.print_exc()
            return False


class ScriptExecutor(BaseExecutor):
    def __init__(self, problem_id, source_code):
        super(ScriptExecutor, self).__init__(problem_id, source_code)
        self._code = self._file(problem_id + self.ext)
        self.create_files(problem_id, source_code)

    def create_files(self, problem_id, source_code):
        with open(self._code, 'wb') as fo:
            fo.write(source_code)


class CompiledExecutor(BaseExecutor):
    def __init__(self, problem_id, source_code, *args, **kwargs):
        super(CompiledExecutor, self).__init__(problem_id, source_code)
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

    def get_compile_process(self):
        return subprocess.Popen(self.get_compile_args(), stderr=subprocess.PIPE, cwd=self._dir,
                                env=self.get_compile_env(), **self.get_compile_popen_kwargs())

    def get_compile_output(self, process):
        return process.communicate()[1]

    def get_compiled_file(self):
        return self._file(self.problem)

    def compile(self):
        process = self.get_compile_process()
        output = self.get_compile_output(process)

        if process.returncode != 0:
            raise CompileError(output)
        self.warning = output
        return self.get_compiled_file()