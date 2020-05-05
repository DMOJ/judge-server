from dmoj.executors.compiled_executor import CompiledExecutor


class Executor(CompiledExecutor):
    ext = 'zig'
    name = 'ZIG'
    command = 'zig'
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

    def get_compile_args(self):
        return [
            self.get_command(),
            'build-exe',
            self._code,
            '--release-safe',
            '--name',
            self.problem,
        ]

    @classmethod
    def get_version_flags(cls, command):
        return ['version']
