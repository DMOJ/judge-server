from dmoj.executors.compiled_executor import CompiledExecutor


class Executor(CompiledExecutor):
    ext = 'zig'
    name = 'ZIG'
    command = 'zig'
    compiler_time_limit = 30
    test_program = '''
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
}'''

    def create_files(self, problem_id, source_code, *args, **kwargs):
        # This cleanup needs to happen because Zig refuses to compile carriage returns.
        # See <https://github.com/ziglang/zig/issues/544>.
        source_code = source_code.replace(b'\r\n', b'\r').replace(b'\r', b'\n')
        super().create_files(problem_id, source_code, *args, **kwargs)

    def get_compile_args(self):
        return [self.get_command(), 'build-exe', self._code, '--release-safe', '--name', self.problem]

    @classmethod
    def get_version_flags(cls, command):
        return ['version']
