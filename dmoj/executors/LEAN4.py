from dmoj.cptbox.filesystem_policies import RecursiveDir
from dmoj.executors.compiled_executor import CompiledExecutor


class Executor(CompiledExecutor):
    ext = 'lean'
    command = 'lean'
    compiler_read_fs = [
        # needed due to snprintf(path, PATH_MAX, "/proc/%d/exe", pid)
        RecursiveDir('/proc'),
    ]
    test_program = """
def main : IO Unit := do
  let cin ← IO.getStdin
  let line ← cin.getLine
  IO.println line
"""

    def compile(self) -> str:
        # lean -c f2.c f1.lean && leanc -o f3 f2.c -O3 -DNDEBUG
        c_file = f'{self.problem}.c'
        proc1 = self.create_compile_process([self.get_command(), '-c', c_file, self._code])
        out1 = self.get_compile_output(proc1)
        proc2 = self.create_compile_process([f'{self.get_command()}c', '-o', self.problem, c_file, '-O3', '-DNDEBUG'])
        out2 = self.get_compile_output(proc2)
        self.warning = b'\n'.join(filter(None, [out1, out2]))
        self._executable = self.get_compiled_file()
        return self._executable
