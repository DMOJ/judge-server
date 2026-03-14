from typing import List

from dmoj.cptbox.filesystem_policies import RecursiveDir
from dmoj.executors.base_executor import VersionFlags
from dmoj.executors.compiled_executor import CompiledExecutor
from dmoj.executors.mixins import StripCarriageReturnsMixin


# Need to strip carriage returns because otherwise Zig refuses to compile.
# See <https://github.com/ziglang/zig/issues/544>.
class Executor(StripCarriageReturnsMixin, CompiledExecutor):
    ext = 'zig'
    command = 'zig'
    compiler_time_limit = 30
    compiler_read_fs = [
        RecursiveDir('~/.cache'),
    ]
    compiler_write_fs = compiler_read_fs
    compiler_required_dirs = ['~/.cache']
    compiler_syscalls = [
        'preadv',
        'pwritev',
        'copy_file_range',
    ]
    test_program = """
const std = @import("std");

pub fn main() !void {
    var buf: [50]u8 = undefined;
    const n = try std.fs.File.stdin().readAll(&buf);
    _ = try std.fs.File.stdout().writeAll(buf[0..n-1]);
}"""

    def get_compile_args(self) -> List[str]:
        command = self.get_command()
        assert command is not None
        assert self._code is not None
        return [command, 'build-exe', self._code, '-fsingle-threaded', '-O', 'ReleaseSafe', '--name', self.problem]

    @classmethod
    def get_version_flags(cls, command: str) -> List[VersionFlags]:
        return ['version']
