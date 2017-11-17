import os

from dmoj.judgeenv import env
from dmoj.executors.base_executor import CompiledExecutor
from dmoj.executors.mixins import NullStdoutMixin

VC_ENV = env['runtime'].get('vc_env', {})
VC_COMPILE = os.environ.copy()

VC_COMPILE.update((k.encode('mbcs'), v.encode('mbcs')) for k, v in
                  env['runtime'].get('vc_compile', VC_ENV).items())
VC_ENV = dict((k.encode('mbcs'), v.encode('mbcs')) for k, v in VC_ENV.items())


class Executor(NullStdoutMixin, CompiledExecutor):
    name = 'VC'
    ext = '.cpp'
    command = 'cl.exe'

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

    def get_compile_args(self):
        return ['cl', '-nologo'] + self.sources + ['-W4', '-DONLINE_JUDGE', '-DWIN32', '-D_CRT_SECURE_NO_WARNINGS',
                                                   '-EHsc', '-Ox', '-Fe%s' % self.get_compiled_file(),
                                                   '-link', '-stack:67108864']

    def get_compile_popen_kwargs(self):
        result = super(Executor, self).get_compile_popen_kwargs()
        result['executable'] = self.get_command()
        return result

    def get_compile_env(self):
        return VC_COMPILE

    def get_env(self):
        return VC_ENV
