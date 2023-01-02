import os
import re

from dmoj.cptbox.filesystem_policies import ExactFile
from dmoj.error import CompileError
from dmoj.executors.compiled_executor import CompiledExecutor

reinline_comment = re.compile(br'//.*?(?=[\r\n])')
recomment = re.compile(br'/\*.*?\*/', re.DOTALL)
repackage = re.compile(br'\s*package\s+main\b')


def decomment(x):
    return reinline_comment.sub(b'', recomment.sub(b'', x))


class Executor(CompiledExecutor):
    ext = 'go'
    nproc = -1
    data_grace = 98304  # Go uses data segment for heap arena map
    address_grace = 786432
    command = 'go'
    syscalls = ['mincore', 'pselect6', 'mlock', 'setrlimit']
    compiler_syscalls = ['setrlimit']
    fs = [
        # Go will start without THP information, but has some tuning for when
        # it is available -- so let's allow it to tell.
        ExactFile('/sys/kernel/mm/transparent_hugepage/hpage_pmd_size'),
    ]
    test_name = 'echo'
    test_program = """\
package main

import "os"
import "fmt"
import "bufio"

func main() {
    bio := bufio.NewReader(os.Stdin)
    text, _ := bio.ReadString(0)
    fmt.Print(text)
}"""

    def get_compile_env(self):
        return {
            # Disable cgo, as it may be used for nefarious things, like linking
            # against arbitrary libraries.
            'CGO_ENABLED': '0',
            # We need GOCACHE to compile on Debian 10.0+.
            'GOCACHE': os.path.join(self._dir, '.cache'),
            # We need to set GOPATH to something on Go 1.16+.
            'GOPATH': '/nonexistent-path',
        }

    def get_compile_args(self):
        return [self.get_command(), 'build', self._code]

    @classmethod
    def get_version_flags(cls, command):
        return ['version']

    def create_files(self, problem_id, source_code, *args, **kwargs):
        source_lines = decomment(source_code).strip().split(b'\n')
        if not repackage.match(source_lines[0]):
            raise CompileError(b'Your code must be defined in package main.\n')
        super().create_files(problem_id, source_code, *args, **kwargs)
