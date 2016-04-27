import os
import subprocess

from wbox import WBoxPopen

from error import CompileError
from .utils import test_executor
from .resource_proxy import ResourceProxy
from judgeenv import env

VC_ENV = env['runtime'].get('vc_env', {})
VC_COMPILE = os.environ.copy()

VC_COMPILE.update((k.encode('mbcs'), v.encode('mbcs')) for k, v in
                  env['runtime'].get('vc_compile', VC_ENV).iteritems())
VC_ENV = dict((k.encode('mbcs'), v.encode('mbcs')) for k, v in VC_ENV.iteritems())


class Executor(ResourceProxy):
    def __init__(self, problem_id, main_source, aux_sources=None):
        super(Executor, self).__init__()

        if not aux_sources:
            aux_sources = {}
        aux_sources[problem_id + '.cpp'] = main_source
        sources = []
        for name, source in aux_sources.iteritems():
            if '.' not in name:
                name += '.cpp'
            with open(self._file(name), 'wb') as fo:
                fo.write(source)
            sources.append(name)
        output_file = self._file('%s.exe' % problem_id)

        cl_args = ['cl', '-nologo'] + sources + ['-W4', '-DONLINE_JUDGE', '-DWIN32', '-D_CRT_SECURE_NO_WARNINGS',
                   '-EHsc', '-Ox', '-Fe%s' % output_file, '-link', '-stack:67108864']
        cl_process = subprocess.Popen(cl_args, stderr=subprocess.PIPE, executable=env['runtime']['cl.exe'],
                                      cwd=self._dir, env=VC_COMPILE)

        _, compile_error = cl_process.communicate()
        if cl_process.returncode != 0:
            raise CompileError(compile_error)
        self._executable = output_file
        self.name = problem_id
        self.warning = compile_error

    def launch(self, *args, **kwargs):
        return WBoxPopen([self.name] + list(args), executable=self._executable,
                         time=kwargs.get('time'), memory=kwargs.get('memory'),
                         cwd=self._dir, env=VC_ENV or None, network_block=True)

    def launch_unsafe(self, *args, **kwargs):
        return subprocess.Popen([self.name] + list(args), executable=self._executable,
                                env=VC_ENV or None, cwd=self._dir, **kwargs)


def initialize(sandbox=True):
    if 'cl.exe' not in env['runtime'] or not os.path.isfile(env['runtime']['cl.exe']):
        return False
    return test_executor('VC', Executor, r'''
#include <iostream>

int main() {
    auto message = "Hello, World!\n";
    std::cout << message;
    return 0;
}
''', sandbox=sandbox)
