from typing import List, Tuple

from dmoj.cptbox.filesystem_policies import ExactFile
from dmoj.executors.base_executor import AutoConfigOutput
from dmoj.executors.java_executor import JavaExecutor


class Executor(JavaExecutor):
    ext = 'kt'

    compiler = 'kotlinc'
    compiler_time_limit = 30
    compiler_read_fs = [
        ExactFile('/bin/uname'),
        ExactFile('/bin/bash'),
    ]
    vm = 'kotlin_vm'

    test_program = """\
fun main(args: Array<String>) {
    println(readLine())
}
"""

    def create_files(self, problem_id: str, source_code: bytes, *args, **kwargs) -> None:
        super().create_files(problem_id, source_code, *args, **kwargs)
        self._jar_name = f'{problem_id}.jar'

    def get_cmdline(self, **kwargs) -> List[str]:
        res = super().get_cmdline(**kwargs)
        res[-2:] = ['-jar', self._jar_name]
        return res

    def get_compile_args(self) -> List[str]:
        compiler = self.get_compiler()
        assert compiler is not None
        assert self._code is not None
        return [compiler, '-include-runtime', '-d', self._jar_name, self._code]

    @classmethod
    def get_versionable_commands(cls) -> List[Tuple[str, str]]:
        compiler = cls.get_compiler()
        vm = cls.get_vm()
        assert compiler is not None
        assert vm is not None
        return [('kotlinc', compiler), ('java', vm)]

    @classmethod
    def autoconfig(cls) -> AutoConfigOutput:
        kotlinc = cls.find_command_from_list(['kotlinc'])
        if kotlinc is None:
            return None, False, 'Failed to find "kotlinc"', ''

        java = cls.find_command_from_list(['java'])
        if java is None:
            return None, False, 'Failed to find "java"', ''

        return cls.autoconfig_run_test({cls.compiler: kotlinc, cls.vm: cls.unravel_java(java)})
