import os
import traceback

from dmoj.error import CompileError
from dmoj.utils import ansi


class GeneratorManager(object):
    def get_generator(self, filename, flags):
        from dmoj.executors import executors

        filename = os.path.abspath(filename)

        try:
            with open(filename, 'r') as file:
                source = file.read()
        except:
            traceback.print_exc()
            raise IOError('could not read generator source')

        def find_runtime(languages):
            for grader in languages:
                if grader in executors:
                    return grader
            return None

        lookup = {
            '.py': executors.get('PY2', None),
            '.py3': executors.get('PY3', None),
            '.c': executors.get('C', None),
            '.cpp': executors.get(find_runtime(('CPP14', 'CPP11', 'CPP0X', 'CPP03')), None),
            '.java': executors.get(find_runtime(('JAVA9', 'JAVA8', 'JAVA7')), None),
            '.rb': executors.get(find_runtime(('RUBY2', 'RUBY19', 'RUBY18')), None)
        }
        ext = os.path.splitext(filename)[1]
        pass_platform_flags = ext in ['.c', '.cpp']

        if pass_platform_flags:
            flags += ['-DWINDOWS_JUDGE', '-DWIN32'] if os.name == 'nt' else ['-DLINUX_JUDGE']

        clazz = lookup.get(ext, None)
        if not clazz:
            raise IOError('could not identify generator extension')
        clazz = clazz.Executor

        if hasattr(clazz, 'flags'):
            # We shouldn't be mutating the base class flags
            # See https://github.com/DMOJ/judge/issues/174
            clazz = type('FlaggedExecutor', (clazz,), {'flags': flags + list(clazz.flags)})

        try:
            from dmoj.executors.base_executor import CompiledExecutor
            kwargs = {}
            # Some generators (like those using testlib.h) take an extremely long time
            # to compile, so we cache them.
            if issubclass(clazz, CompiledExecutor):
                kwargs['cached'] = True
            executor = clazz('_generator', source, **kwargs)
        except CompileError as err:
            # Strip ansi codes from CompileError message so we don't get wacky displays on the site like
            # 01m[K_generator.cpp:26:23:[m[K [01;31m[Kerror: [m[K'[01m[Kgets[m[K' was not declared in this scope
            raise CompileError(ansi.strip_ansi(err.args[0]))

        return executor
