import os

from dmoj.executors.compiled_executor import CompiledExecutor
from dmoj.judgeenv import env


class Executor(CompiledExecutor):
    ext = 'zig'
    name = 'ZIG'
    command = 'zig'
    test_program = '''
const std = @import("std");

pub fn main() !void {
    const stdout = std.io.getStdOut().outStream();
    try stdout.print("echo: Hello, {}!\\n", .{"World"});
}'''

    def get_compile_args(self):
        return [
            self.get_command(), 
            'build-exe',
            self._code,
            '--name',
            self.problem,
        ]

    @classmethod
    def get_version_flags(cls, command):
        return ['version']
