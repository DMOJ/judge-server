import errno
import io
import mmap
import os
from typing import Optional

from dmoj.cptbox._cptbox import memory_fd_create, memory_fd_seal


class MemoryIO(io.FileIO):
    def __init__(self, prefill: Optional[bytes] = None, seal=False) -> None:
        super().__init__(memory_fd_create(), 'r+')
        if prefill:
            self.write(prefill)
        if seal:
            self.seal()

    def seal(self) -> None:
        fd = self.fileno()
        try:
            memory_fd_seal(fd)
        except OSError as e:
            if e.errno == errno.ENOSYS:
                # FreeBSD
                self.seek(0, os.SEEK_SET)
                return
            raise

        new_fd = os.open(f'/proc/self/fd/{fd}', os.O_RDONLY)
        try:
            os.dup2(new_fd, fd)
        finally:
            os.close(new_fd)

    def to_path(self) -> str:
        return f'/proc/{os.getpid()}/fd/{self.fileno()}'

    def to_bytes(self) -> bytes:
        try:
            with mmap.mmap(self.fileno(), 0, access=mmap.ACCESS_READ) as f:
                return bytes(f)
        except ValueError as e:
            if e.args[0] == 'cannot mmap an empty file':
                return b''
            raise
