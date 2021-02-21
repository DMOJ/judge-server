import os
import tempfile

from dmoj.error import InternalError
from dmoj.result import Result
from dmoj.utils.os_ext import strsignal


def mktemp(data):
    tmp = tempfile.NamedTemporaryFile()
    tmp.write(data)
    tmp.flush()
    return tmp


def compile_with_auxiliary_files(filenames, flags=[], lang=None, compiler_time_limit=None, should_cache=True):
    from dmoj.executors import executors
    from dmoj.executors.compiled_executor import CompiledExecutor

    sources = {}

    for filename in filenames:
        with open(filename, 'rb') as f:
            sources[os.path.basename(filename)] = f.read()

    def find_runtime(languages):
        for grader in languages:
            if grader in executors:
                return grader
        return None

    use_cpp = any(map(lambda name: os.path.splitext(name)[1] in ['.cpp', '.cc'], filenames))
    use_c = any(map(lambda name: os.path.splitext(name)[1] in ['.c'], filenames))
    if lang is None:
        best_choices = ('CPP20', 'CPP17', 'CPP14', 'CPP11', 'CPP03') if use_cpp else ('C11', 'C')
        lang = find_runtime(best_choices)

    executor = executors.get(lang)
    if not executor:
        raise IOError('could not find an appropriate C++ executor')

    executor = executor.Executor

    kwargs = {'fs': executor.fs + [tempfile.gettempdir()]}

    if issubclass(executor, CompiledExecutor):
        kwargs['compiler_time_limit'] = compiler_time_limit

    if hasattr(executor, 'flags'):
        kwargs['flags'] = flags + list(executor.flags)

    # Optimize the common case.
    if use_cpp or use_c:
        # Some auxiliary files (like those using testlib.h) take an extremely long time to compile, so we cache them.
        executor = executor('_aux_file', None, aux_sources=sources, cached=should_cache, **kwargs)
    else:
        if len(sources) > 1:
            raise InternalError('non-C/C++ auxilary programs cannot be multi-file')
        executor = executor('_aux_file', list(sources.values())[0], **kwargs)

    return executor


def parse_helper_file_error(proc, executor, name, stderr, time_limit, memory_limit):
    if proc.is_tle:
        error = '%s timed out (> %d seconds)' % (name, time_limit)
    elif proc.is_mle:
        error = '%s ran out of memory (> %s Kb)' % (name, memory_limit)
    elif proc.protection_fault:
        syscall, callname, args, update_errno = proc.protection_fault
        error = '%s invoked disallowed syscall %s (%s)' % (name, syscall, callname)
    elif proc.returncode:
        if proc.returncode > 0:
            error = '%s exited with nonzero code %d' % (name, proc.returncode)
        else:
            error = '%s exited with %s' % (name, strsignal(proc.signal))
        feedback = Result.get_feedback_str(stderr, proc, executor)
        if feedback:
            error += ' with feedback %s' % feedback
    else:
        return

    raise InternalError(error)
