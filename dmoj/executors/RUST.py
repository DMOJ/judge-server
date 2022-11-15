import fcntl
import os

from dmoj.cptbox.filesystem_policies import ExactFile, RecursiveDir
from dmoj.executors.compiled_executor import CompiledExecutor

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

    def __init__(self, problem_id: str, source_code: bytes, **kwargs) -> None:
        super().__init__(problem_id, source_code, **kwargs)
        self.shared_target = None

    def create_files(self, problem_id, source_code, *args, **kwargs):
        os.mkdir(self._file('src'))
        with open(self._file('src', 'main.rs'), 'wb') as f:
            f.write(source_code)

        with open(self._file('Cargo.toml'), 'wb') as f:
            f.write(CARGO_TOML)

    def get_shared_target(self):
        if self.shared_target is not None:
            return self.shared_target

        cargo_dir = os.path.expanduser('~/.cargo')
        collisions = 0
        while True:
            maybe_target = os.path.join(cargo_dir, f'dmoj-shared-target-{collisions}')
            try:
                os.mkdir(maybe_target, mode=0o775)
            except FileExistsError:
                pass

            dirfd = os.open(maybe_target, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
            try:
                fcntl.flock(dirfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                # Another judge is using this.
                os.close(dirfd)
                collisions += 1
            else:
                self.shared_target_dirfd = dirfd
                self.shared_target = maybe_target
                # We intentionally don't clean this directory up at any point, since we can re-use it.
                return self.shared_target

    def cleanup(self) -> None:
        super().cleanup()
        if self.shared_target is not None:
            # Closing also unlocks.
            os.close(self.shared_target_dirfd)

    @classmethod
    def get_versionable_commands(cls):
        return [('rustc', os.path.join(os.path.dirname(cls.get_command()), 'rustc'))]

    def get_compile_args(self):
        args = [self.get_command(), 'build', '--release', '--offline', '--target-dir', self.get_shared_target()]
        return args

    def get_compiled_file(self):
        return os.path.join(self.get_shared_target(), 'release/user_submission')
