import os
import tempfile
from typing import IO, List, Optional, Sequence, TYPE_CHECKING

from dmoj.cptbox.filesystem_policies import RecursiveDir
from dmoj.error import InternalError
from dmoj.result import Result
from dmoj.utils.os_ext import strsignal

if TYPE_CHECKING:
    from dmoj.executors.base_executor import BaseExecutor


def mktemp(data: bytes) -> IO:
    tmp = tempfile.NamedTemporaryFile()
    tmp.write(data)
    tmp.flush()
    return tmp


def compile_with_auxiliary_files(
    filenames: Sequence[str],
    flags: List[str] = [],
    lang: Optional[str] = None,
    compiler_time_limit: Optional[int] = None,
    unbuffered: bool = False,
) -> 'BaseExecutor':
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

    kwargs = {'fs': executor.fs + [RecursiveDir(tempfile.gettempdir())]}

    if issubclass(executor, CompiledExecutor):
        kwargs['compiler_time_limit'] = compiler_time_limit

    if hasattr(executor, 'flags'):
        kwargs['flags'] = flags + list(executor.flags)

    # Optimize the common case.
    if use_cpp or use_c:
        # Some auxiliary files (like those using testlib.h) take an extremely long time to compile, so we cache them.
        executor = executor('_aux_file', None, aux_sources=sources, cached=True, unbuffered=unbuffered, **kwargs)
    else:
        if len(sources) > 1:
            raise InternalError('non-C/C++ auxilary programs cannot be multi-file')
        executor = executor('_aux_file', list(sources.values())[0], cached=True, unbuffered=unbuffered, **kwargs)

    return executor


def parse_helper_file_error(proc, executor, name: str, stderr: bytes, time_limit: int, memory_limit: int) -> None:
    if proc.is_tle:
        error = f'{name} timed out (> {time_limit} seconds)'
    elif proc.is_mle:
        error = f'{name} ran out of memory (> {memory_limit} KB)'
    elif proc.protection_fault:
        syscall, callname, args, update_errno = proc.protection_fault
        error = f'{name} invoked disallowed syscall {syscall} ({callname})'
    elif proc.returncode:
        if proc.returncode > 0:
            error = f'{name} exited with nonzero code {proc.returncode:d}'
        else:
            error = f'{name} exited with {strsignal(proc.signal)}'
        feedback = Result.get_feedback_str(stderr, proc, executor)
        if feedback:
            error += f' with feedback {feedback}'
    else:
        return

    raise InternalError(error)
