import io
import mmap
import os
from abc import ABCMeta, abstractmethod
from tempfile import NamedTemporaryFile, TemporaryFile
from typing import Optional

from dmoj.cptbox._cptbox import memfd_create, memfd_seal


def _make_fd_readonly(fd):
    new_fd = os.open(f'/proc/self/fd/{fd}', os.O_RDONLY)
    try:
        os.dup2(new_fd, fd)
    finally:
        os.close(new_fd)


class MmapableIO(io.FileIO, metaclass=ABCMeta):
    def __init__(self, fd, *, prefill: Optional[bytes] = None, seal=False) -> None:
        super().__init__(fd, 'r+')

        if prefill:
            self.write(prefill)
        if seal:
            self.seal()

    @classmethod
    @abstractmethod
    def usable_with_name(cls) -> bool:
        ...

    @abstractmethod
    def seal(self) -> None:
        ...

    @abstractmethod
    def to_path(self) -> str:
        ...

    def to_bytes(self) -> bytes:
        try:
            with mmap.mmap(self.fileno(), 0, access=mmap.ACCESS_READ) as f:
                return bytes(f)
        except ValueError as e:
            if e.args[0] == 'cannot mmap an empty file':
                return b''
            raise


class NamedFileIO(MmapableIO):
    _name: str

    def __init__(self, *, prefill: Optional[bytes] = None, seal=False) -> None:
        with NamedTemporaryFile(delete=False) as f:
            self._name = f.name
            super().__init__(os.dup(f.fileno()), prefill=prefill, seal=seal)

    def seal(self) -> None:
        self.seek(0, os.SEEK_SET)

    def close(self) -> None:
        super().close()
        os.unlink(self._name)

    def to_path(self) -> str:
        return self._name

    @classmethod
    def usable_with_name(cls):
        return True


class UnnamedFileIO(MmapableIO):
    def __init__(self, *, prefill: Optional[bytes] = None, seal=False) -> None:
        with TemporaryFile() as f:
            super().__init__(os.dup(f.fileno()), prefill=prefill, seal=seal)

    def seal(self) -> None:
        self.seek(0, os.SEEK_SET)
        _make_fd_readonly(self.fileno())

    def to_path(self) -> str:
        return f'/proc/{os.getpid()}/fd/{self.fileno()}'

    @classmethod
    def usable_with_name(cls):
        with cls() as f:
            return os.path.exists(f.to_path())


class MemfdIO(MmapableIO):
    def __init__(self, *, prefill: Optional[bytes] = None, seal=False) -> None:
        super().__init__(memfd_create(), prefill=prefill, seal=seal)

    def seal(self) -> None:
        fd = self.fileno()
        memfd_seal(fd)
        _make_fd_readonly(fd)

    def to_path(self) -> str:
        return f'/proc/{os.getpid()}/fd/{self.fileno()}'

    @classmethod
    def usable_with_name(cls):
        try:
            with cls() as f:
                return os.path.exists(f.to_path())
        except OSError:
            return False


# Try to use memfd if possible, otherwise fallback to unlinked temporary files
# (UnnamedFileIO). On FreeBSD and some other systems, /proc/[pid]/fd doesn't
# exist, so to_path() will not work. We fall back to NamedFileIO in that case.
MemoryIO = next((i for i in (MemfdIO, UnnamedFileIO, NamedFileIO) if i.usable_with_name()))
