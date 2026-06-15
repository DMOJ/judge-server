import os
import tempfile
from typing import IO, List, Optional, Sequence, TYPE_CHECKING

from dmoj.cptbox.filesystem_policies import RecursiveDir
from dmoj.error import InternalError
from dmoj.result import Result
from dmoj.utils.os_ext import strsignal

if TYPE_CHECKING:
    from dmoj.cptbox import TracedPopen
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
    from dmoj import executors
    from dmoj.executors.compiled_executor import CompiledExecutor

    sources = {}

    for filename in filenames:
        with open(filename, 'rb') as f:
            sources[os.path.basename(filename)] = f.read()

    if not lang:
        for filename in filenames:
            try:
                lang = executors.from_filename(filename).Executor.name
            except KeyError:
                continue

    if not lang:
        raise IOError('could not find an appropriate executor')

    executor = executors.executors[lang].Executor

    kwargs = {'fs': executor.fs + [RecursiveDir(tempfile.gettempdir())]}

    if issubclass(executor, CompiledExecutor):
        kwargs['compiler_time_limit'] = compiler_time_limit

    if hasattr(executor, 'flags'):
        kwargs['flags'] = flags + executor.flags

    # Check if the executor supports multifile compilation
    if executor.supports_multifile():
        # Some auxiliary files (like those using testlib.h) take an extremely long time to compile, so we cache them.
        executor = executor('_aux_file', None, aux_sources=sources, cached=True, unbuffered=unbuffered, **kwargs)
    else:
        if len(sources) > 1:
            raise InternalError(f'{lang} auxiliary programs cannot be multi-file')
        executor = executor('_aux_file', list(sources.values())[0], cached=True, unbuffered=unbuffered, **kwargs)

    return executor


def parse_helper_file_error(
    proc: 'TracedPopen', executor: 'BaseExecutor', name: str, stderr: bytes, time_limit: float, memory_limit: int
) -> None:
    if proc.is_tle:
        error = f'{name} timed out (> {time_limit} seconds)'
    elif proc.is_mle:
        error = f'{name} ran out of memory (> {memory_limit} KB)'
    elif proc.protection_fault:
        syscall, callname, args, update_errno = proc.protection_fault
        error = f'{name} invoked disallowed syscall {syscall} ({callname})'
    elif proc.returncode:
        if proc.returncode > 0:
            error = f'{name} exited with nonzero code {proc.returncode}'
        else:
            assert proc.signal is not None
            error = f'{name} exited with {strsignal(proc.signal)}'
        feedback = Result.get_feedback_str(stderr, proc, executor)
        if feedback:
            error += f' with feedback {feedback}'
    else:
        return

    raise InternalError(error)
