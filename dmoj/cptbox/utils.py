import io

from dmoj.cptbox._cptbox import memory_fd_create, memory_fd_seal


class MemoryIO(io.FileIO):
    def __init__(self) -> None:
        super().__init__(memory_fd_create(), 'r+')

    def seal(self) -> None:
        memory_fd_seal(self.fileno())
