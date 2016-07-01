from dmoj.executors.base_executor import CompiledExecutor
from dmoj.judgeenv import env


class Executor(CompiledExecutor):
    ext = '.ml'
    name = 'OCAML'
    command = 'ocaml'
    test_program = 'print_endline (input_line stdin)'

    def get_compile_args(self):
        return [env['runtime']['ocaml'], self._code, '-o', self.problem]
