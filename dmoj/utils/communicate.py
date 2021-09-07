import errno
import os
import select
from typing import Dict, IO, List, Optional, Tuple

from dmoj.error import OutputLimitExceeded

_PIPE_BUF = getattr(select, 'PIPE_BUF', 512)


def safe_communicate(
    proc, input: Optional[bytes] = None, outlimit: Optional[int] = None, errlimit: Optional[int] = None
) -> Tuple[bytes, bytes]:
    if outlimit is None:
        outlimit = 10485760
    if errlimit is None:
        errlimit = outlimit
    if proc.stdin:
        # Flush stdio buffer.  This might block, if the user has
        # been writing to .stdin in an uncontrolled fashion.
        proc.stdin.flush()
        if not input:
            proc.stdin.close()

    stdout_list: Optional[List[bytes]] = None  # Return
    stderr_list: Optional[List[bytes]] = None  # Return
    fd2file: Dict[int, IO] = {}
    fd2output: Dict[int, List[bytes]] = {}
    fd2length: Dict[int, int] = {}
    fd2limit: Dict[int, int] = {}

    poller = select.poll()

    def register_and_append(file_obj, eventmask):
        poller.register(file_obj.fileno(), eventmask)
        fd2file[file_obj.fileno()] = file_obj

    def close_unregister_and_remove(fd):
        poller.unregister(fd)
        fd2file[fd].close()
        fd2file.pop(fd)

    if proc.stdin and input:
        register_and_append(proc.stdin, select.POLLOUT)

    select_POLLIN_POLLPRI = select.POLLIN | select.POLLPRI
    if proc.stdout:
        register_and_append(proc.stdout, select_POLLIN_POLLPRI)
        fd2output[proc.stdout.fileno()] = stdout_list = []
        fd2length[proc.stdout.fileno()] = 0
        fd2limit[proc.stdout.fileno()] = outlimit
    if proc.stderr:
        register_and_append(proc.stderr, select_POLLIN_POLLPRI)
        fd2output[proc.stderr.fileno()] = stderr_list = []
        fd2length[proc.stderr.fileno()] = 0
        fd2limit[proc.stderr.fileno()] = errlimit

    input_offset = 0
    while fd2file:
        try:
            ready = poller.poll()
        except select.error as e:
            if e.args[0] == errno.EINTR:
                continue
            raise

        for fd, mode in ready:
            if mode & select.POLLOUT:
                assert input
                chunk = input[input_offset : input_offset + _PIPE_BUF]
                try:
                    input_offset += os.write(fd, chunk)
                except OSError as e:
                    if e.errno == errno.EPIPE:
                        close_unregister_and_remove(fd)
                    else:
                        raise
                else:
                    if input_offset >= len(input):
                        close_unregister_and_remove(fd)
            elif mode & select_POLLIN_POLLPRI:
                data = os.read(fd, 4096)
                if not data:
                    close_unregister_and_remove(fd)
                fd2output[fd].append(data)
                fd2length[fd] += len(data)
                if fd2length[fd] > fd2limit[fd]:
                    proc.mark_ole()
                    raise OutputLimitExceeded(
                        'stdout' if proc.stdout is not None and proc.stdout.fileno() == fd else 'stderr', fd2limit[fd]
                    )
            else:
                # Ignore hang up or errors.
                close_unregister_and_remove(fd)

    # All data exchanged.  Translate lists into strings.
    stdout = b''.join(stdout_list) if stdout_list is not None else b''
    stderr = b''.join(stderr_list) if stderr_list is not None else b''

    proc.wait()
    return stdout, stderr
