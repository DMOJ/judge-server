from dmoj.cptbox.filesystem_policies import RecursiveDir
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
    test_program = """
const std = @import("std");

pub fn main() !void {
    const io = std.io;
    const stdin = std.io.getStdIn().inStream();
    const stdout = std.io.getStdOut().outStream();

    var line_buf: [50]u8 = undefined;
    while (try stdin.readUntilDelimiterOrEof(&line_buf, '\n')) |line| {
        if (line.len == 0) break;
        try stdout.print("{}", .{line});
    }
}"""

    def get_compile_args(self):
        return [self.get_command(), 'build-exe', self._code, '--release-safe', '--name', self.problem]

    @classmethod
    def get_version_flags(cls, command):
        return ['version']
