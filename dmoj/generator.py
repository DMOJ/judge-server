import os
import traceback

from dmoj.error import CompileError, InternalError
from dmoj.utils import ansi


class GeneratorManager(object):
    def get_generator(self, filenames, flags, lang=None, compiler_time_limit=None):
        from dmoj.executors import executors
        from dmoj.executors.base_executor import CompiledExecutor

        filenames = list(map(os.path.abspath, filenames))
        sources = {}

        try:
            for filename in filenames:
                with open(filename, 'r') as f:
                    sources[os.path.basename(filename)] = f.read()
        except:
            traceback.print_exc()
            raise IOError('could not read generator source')

        def find_runtime(languages):
            for grader in languages:
                if grader in executors:
                    return grader
            return None

        use_cpp = any(map(lambda name: os.path.splitext(name)[1] == '.cpp', filenames))
        if lang is None:
            best_choices = ('CPP17', 'CPP14', 'CPP11', 'CPP0X', 'CPP03') if use_cpp else ('C11', 'C')
            lang = find_runtime(best_choices)

        clazz = executors.get(lang)
        if not clazz:
            raise IOError('could not find a C++ executor for generator')

        clazz = clazz.Executor

        if issubclass(clazz, CompiledExecutor):
            compiler_time_limit = compiler_time_limit or clazz.compiler_time_limit
            clazz = type('Executor', (clazz,), {'compiler_time_limit': compiler_time_limit})

        try:
            # Optimize the common case.
            if use_cpp:
                # Some generators (like those using testlib.h) take an extremely long time
                # to compile, so we cache them.
                executor = clazz('_generator', None, aux_sources=sources, cached=True)
            else:
                if len(sources) > 1:
                    raise InternalError('non-C/C++ generator cannot be multi-file')
                executor = clazz('_generator', list(sources.values())[0])
        except CompileError as err:
            # Strip ANSI codes from CompileError message so we don't get wacky displays on the site like
            # 01m[K_generator.cpp:26:23:[m[K [01;31m[Kerror: [m[K'[01m[Kgets[m[K' was not declared in this scope
            raise CompileError(ansi.strip_ansi(err.args[0]))

        return executor
