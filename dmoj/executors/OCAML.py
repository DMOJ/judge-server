from typing import List, Tuple

from dmoj.cptbox.filesystem_policies import RecursiveDir
from dmoj.executors.base_executor import VersionFlags
from dmoj.executors.compiled_executor import CompiledExecutor


# We default to a "more-than-vanilla" OCaml. In particular, we compile with
# Jane Street Base, Core, and Stdio packages, as well as Zarith. These need a
# functioning opam + ocamlfind installation to work.
class Executor(CompiledExecutor):
    ext = 'ml'
    command = 'ocamlfind'
    compiler_read_fs = [
        RecursiveDir('~/.opam'),
    ]
    test_program = """
open! Base
open! Core
open! Stdio

let () = (In_channel.iter_lines Stdio.stdin ~f:print_endline)
"""

    # Space for major / minor heaps is reserved ahead of time.
    address_grace = 256 * 1024

    def get_compile_args(self) -> List[str]:
        assert self._code is not None
        # fmt: off
        return [
            self.runtime_dict['ocamlfind'],
            'opt',
            '-package', 'str',
            '-package', 'base',
            '-package', 'core',
            '-package', 'stdio',
            '-package', 'zarith',
            '-thread',
            '-linkpkg',
            self._code,
            '-o',
            self.problem,
        ]
        # fmt: on

    @classmethod
    def get_version_flags(cls, command: str) -> List[VersionFlags]:
        return [('opt', '-version')]

    @classmethod
    def get_versionable_commands(cls) -> List[Tuple[str, str]]:
        command = cls.get_command()
        assert command is not None
        return [('ocaml', command)]
