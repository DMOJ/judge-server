import os

from .base_executor import CompiledExecutor

CARGO_TOML = b'''\
[package]
name = "user_submission"
version = "1.0.0"

[dependencies]
dmoj = "0.1"
rand = "0.3"
'''

CARGO_LOCK = b'''\
[root]
name = "user_submission"
version = "1.0.0"
dependencies = [
 "dmoj 0.1.5 (registry+https://github.com/rust-lang/crates.io-index)",
 "rand 0.3.15 (registry+https://github.com/rust-lang/crates.io-index)",
]

[[package]]
name = "dmoj"
version = "0.1.5"
source = "registry+https://github.com/rust-lang/crates.io-index"
dependencies = [
 "lazy_static 0.2.2 (registry+https://github.com/rust-lang/crates.io-index)",
 "libc 0.2.18 (registry+https://github.com/rust-lang/crates.io-index)",
]

[[package]]
name = "lazy_static"
version = "0.2.2"
source = "registry+https://github.com/rust-lang/crates.io-index"

[[package]]
name = "libc"
version = "0.2.18"
source = "registry+https://github.com/rust-lang/crates.io-index"

[[package]]
name = "rand"
version = "0.3.15"
source = "registry+https://github.com/rust-lang/crates.io-index"
dependencies = [
 "libc 0.2.18 (registry+https://github.com/rust-lang/crates.io-index)",
]

[metadata]
"checksum dmoj 0.1.5 (registry+https://github.com/rust-lang/crates.io-index)" = "a1f8a155771d562ab98db35ed9b4da482ef178eec293eeb1f6302036100e84f1"
"checksum lazy_static 0.2.2 (registry+https://github.com/rust-lang/crates.io-index)" = "6abe0ee2e758cd6bc8a2cd56726359007748fbf4128da998b65d0b70f881e19b"
"checksum libc 0.2.18 (registry+https://github.com/rust-lang/crates.io-index)" = "a51822fc847e7a8101514d1d44e354ba2ffa7d4c194dcab48870740e327cac70"
"checksum rand 0.3.15 (registry+https://github.com/rust-lang/crates.io-index)" = "022e0636ec2519ddae48154b028864bdce4eaf7d35226ab8e65c611be97b189d"
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
    compiler_time_limit = 20

    def create_files(self, problem_id, source_code, *args, **kwargs):
        os.mkdir(self._file('src'))
        with open(self._file('src', 'main.rs'), 'wb') as f:
            f.write(source_code)

        with open(self._file('Cargo.toml'), 'wb') as f:
            f.write(CARGO_TOML)

        with open(self._file('Cargo.lock'), 'wb') as f:
            f.write(CARGO_LOCK)

    def get_compile_args(self):
        return [self.get_command(), 'build', '--release']

    def get_compiled_file(self):
        return self._file('target', 'release', 'user_submission')
