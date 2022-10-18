import os

from dmoj.cptbox.filesystem_policies import ExactFile, RecursiveDir
from dmoj.executors.compiled_executor import CompiledExecutor
from dmoj.utils.os_ext import bool_env

CARGO_TOML = b"""\
[package]
name = "user_submission"
version = "1.0.0"
edition = "2021"

[dependencies]
dmoj = "0.1"
libc = "0.2"
rand = "0.8"
rand_xoshiro = "0.6"

[profile.release]
strip = "symbols"
"""

TEST_PROGRAM = """\
// Sanity-check our libraries
use dmoj as _;
use libc as _;
use rand as _;
use rand_xoshiro as _;

use std::io;
fn main() -> io::Result<()> {
    io::copy(&mut io::stdin(), &mut io::stdout())?;
    Ok(())
}
"""


class Executor(CompiledExecutor):
    ext = 'rs'
    command = 'cargo'
    test_program = TEST_PROGRAM
    compiler_time_limit = 20
    compiler_read_fs = [
        RecursiveDir('/home'),
        ExactFile('/etc/resolv.conf'),
    ]
    compiler_write_fs = [
        RecursiveDir('~/.cargo'),
    ]

    def create_files(self, problem_id, source_code, *args, **kwargs):
        os.mkdir(self._file('src'))
        with open(self._file('src', 'main.rs'), 'wb') as f:
            f.write(source_code)

        with open(self._file('Cargo.toml'), 'wb') as f:
            f.write(CARGO_TOML)

    @classmethod
    def get_versionable_commands(cls):
        return [('rustc', os.path.join(os.path.dirname(cls.get_command()), 'rustc'))]

    def get_compile_args(self):
        args = [self.get_command(), 'build', '--release']
        if bool_env('DMOJ_CARGO_OFFLINE'):
            args += ['--offline']
        return args

    def get_compiled_file(self):
        return self._file('target', 'release', 'user_submission')
