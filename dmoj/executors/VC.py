import os

from dmoj.judgeenv import env
from .base_executor import CompiledExecutor

VC_ENV = env['runtime'].get('vc_env', {})
VC_COMPILE = os.environ.copy()

VC_COMPILE.update((k.encode('mbcs'), v.encode('mbcs')) for k, v in
                  env['runtime'].get('vc_compile', VC_ENV).iteritems())
VC_ENV = dict((k.encode('mbcs'), v.encode('mbcs')) for k, v in VC_ENV.iteritems())


class Executor(CompiledExecutor):
    name = 'VC'
    ext = '.cpp'
    command = env['runtime'].get('cl.exe')

    test_program = r'''
#include <iostream>

int main() {
    auto message = std::cin.rdbuf();
    std::cout << message;
    return 0;
}
'''

    def create_files(self, problem_id, main_source, aux_sources=None, *args, **kwargs):
        if not aux_sources:
            aux_sources = {}
        aux_sources[problem_id + self.ext] = main_source
        sources = []
        for name, source in aux_sources.iteritems():
            if '.' not in name:
                name += self.ext
            with open(self._file(name), 'wb') as fo:
                fo.write(source)
            sources.append(name)
        self.sources = sources
        self.devnull = open(os.devnull, 'w')

    def cleanup(self):
        self.devnull.close()
        super(Executor, self).cleanup()

    def get_compile_args(self):
        return ['cl', '-nologo'] + self.sources + ['-W4', '-DONLINE_JUDGE', '-DWIN32', '-D_CRT_SECURE_NO_WARNINGS',
                                                   '-EHsc', '-Ox', '-Fe%s' % self.get_compiled_file(),
                                                   '-link', '-stack:67108864']

    def get_compile_popen_kwargs(self):
        return {'executable': self.get_command(), 'stdout': self.devnull}

    def get_compile_env(self):
        return VC_COMPILE

    def get_env(self):
        return VC_ENV

initialize = Executor.initialize
