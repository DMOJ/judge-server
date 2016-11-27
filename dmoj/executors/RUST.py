import os

from .base_executor import CompiledExecutor


CARGO_TOML = '''\
[package]
name = "user_submission"
version = "1.0.0"

[dependencies]
dmoj = "0.1"
rand = "0.3"
'''

HELLO_WORLD_PROGRAM = '''\
#[macro_use] extern crate dmoj;
extern crate rand;

fn main() {
    println!("echo: Hello, World!");
}
'''


class Executor(CompiledExecutor):
    name = 'RUST'
    command = 'cargo'
    test_program = HELLO_WORLD_PROGRAM

    def create_files(self, problem_id, source_code, *args, **kwargs):
        os.mkdir(self._file('src'))
        with open(self._file('src', 'main.rs'), 'wb') as f:
            f.write(source_code)

        with open(self._file('Cargo.toml'), 'wb') as f:
            f.write(CARGO_TOML)

    def get_compile_args(self):
        return [self.get_command(), 'build', '--release']

    def get_compiled_file(self):
        return self._file('target', 'release', 'user_submission')
