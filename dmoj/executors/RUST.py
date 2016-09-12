import os

from .base_executor import CompiledExecutor


CARGO_TOML = '''\
[package]
name = "{name}"
version = "0.0.0"
'''


class Executor(CompiledExecutor):
    name = 'RUST'
    command = 'cargo'
    test_program = 'fn main() { println!("echo: Hello, World!"); }'

    def create_files(self, problem_id, source_code, *args, **kwargs):
        os.mkdir(self._file('src'))
        with open(self._file(os.path.join('src', 'main.rs')), 'wb') as f:
            f.write(source_code)

        with open(self._file('Cargo.toml'), 'wb') as f:
            f.write(CARGO_TOML.format(name=problem_id))

    def get_compile_args(self):
        return [self.get_command(), 'build', '--release']

    def get_compiled_file(self):
        return self._file(os.path.join('target', 'release', self.problem))
