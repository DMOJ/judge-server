import os
import subprocess
import sys

try:
    from cptbox import CHROOTSecurity, SecurePopen, PIPE
except ImportError:
    CHROOTSecurity, SecurePopen, PIPE = None, None, None

from error import CompileError
from .utils import test_executor
from .resource_proxy import ResourceProxy
from judgeenv import env

C_FS = ['.*\.so', '/proc/meminfo', '/dev/null']

GCC_ENV = env['runtime'].get('gcc_env', {})
GCC_COMPILE = os.environ.copy()

if os.name == 'nt':
    GCC_COMPILE.update((k.encode('mbcs'), v.encode('mbcs')) for k, v in
                       env['runtime'].get('gcc_compile', GCC_ENV).iteritems())
    GCC_ENV = dict((k.encode('mbcs'), v.encode('mbcs')) for k, v in GCC_ENV.iteritems())
else:
    GCC_COMPILE.update(env['runtime'].get('gcc_compile', {}))


def make_executor(code, command, args, ext, test_code):
    class Executor(ResourceProxy):
        def __init__(self, problem_id, main_source, aux_sources=None, fds=None, writable=(1, 2)):
            super(Executor, self).__init__()
            if not aux_sources:
                aux_sources = {}
            aux_sources[problem_id + ext] = main_source
            sources = []
            for name, source in aux_sources.iteritems():
                if '.' not in name:
                    name += ext
                with open(self._file(name), 'wb') as fo:
                    fo.write(source)
                sources.append(name)
            if sys.platform == 'win32':
                compiled_extension = '.exe'
                linker_options = ['-Wl,--stack,67108864']
            else:
                compiled_extension = ''
                linker_options = []
            output_file = self._file('%s%s' % (problem_id, compiled_extension))
            gcc_args = ([env['runtime'][command]] + sources + ['-Wall', '-DONLINE_JUDGE', '-O2', '-lm', '-march=native'] + args +
                        linker_options + ['-s', '-o', output_file])

            gcc_process = subprocess.Popen(gcc_args, stderr=subprocess.PIPE, executable=env['runtime'][command],
                                           cwd=self._dir, env=GCC_COMPILE)
            _, compile_error = gcc_process.communicate()
            if gcc_process.returncode != 0:
                raise CompileError(compile_error)
            self._executable = output_file
            self.name = problem_id
            self._fds = fds
            self._writable = writable
            self.warning = compile_error

        if SecurePopen is not None:
            def launch(self, *args, **kwargs):
                return SecurePopen([self.name] + list(args),
                                   executable=self._executable,
                                   security=CHROOTSecurity(C_FS, writable=self._writable),
                                   time=kwargs.get('time'),
                                   memory=kwargs.get('memory'),
                                   stderr=(PIPE if kwargs.get('pipe_stderr', False) else None),
                                   env=GCC_ENV,
                                   cwd=self._dir, fds=self._fds)

        def launch_unsafe(self, *args, **kwargs):
            return subprocess.Popen([self.name] + list(args),
                                    executable=self._executable,
                                    env=GCC_ENV,
                                    cwd=self._dir,
                                    **kwargs)

    def initialize():
        if command not in env['runtime'] or SecurePopen is None:
            return False
        if not os.path.isfile(env['runtime'][command]):
            return False
        return test_executor(code, Executor, test_code)

    return Executor, initialize
