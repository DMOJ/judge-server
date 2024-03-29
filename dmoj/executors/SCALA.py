import os
import subprocess
from typing import List, Tuple

from dmoj.cptbox.filesystem_policies import ExactFile, RecursiveDir
from dmoj.executors.base_executor import AutoConfigOutput, AutoConfigResult
from dmoj.executors.java_executor import JavaExecutor
from dmoj.utils.unicode import utf8text


# Must emulate terminal, otherwise `scalac` hangs on a call to `stty`
class Executor(JavaExecutor):
    ext = 'scala'

    compiler = 'scalac'
    compiler_time_limit = 20
    compiler_read_fs = [
        ExactFile('/bin/uname'),
        ExactFile('/bin/readlink'),
        ExactFile('/bin/grep'),
        ExactFile('/bin/stty'),
        ExactFile('/bin/bash'),
        RecursiveDir('/etc/alternatives'),
    ]
    vm = 'scala_vm'

    test_program = """\
object self_test extends App {
     println("echo: Hello, World!")
}
"""

    def create_files(self, problem_id: str, source_code: bytes, *args, **kwargs) -> None:
        super().create_files(problem_id, source_code, *args, **kwargs)
        self._class_name = problem_id

    def get_cmdline(self, **kwargs) -> List[str]:
        res = super().get_cmdline(**kwargs)

        # Simply run bash -x $(which scala) and copy all arguments after -Xmx and -Xms
        # and add it as a list in the configuration.
        res[-2:-1] = self.runtime_dict['scala_args']
        return res

    def get_compile_args(self):
        compiler = self.get_compiler()
        assert compiler is not None
        assert self._code is not None
        return [compiler, self._code]

    @classmethod
    def get_versionable_commands(cls) -> List[Tuple[str, str]]:
        compiler = cls.get_compiler()
        vm = cls.get_vm()
        assert compiler is not None
        assert vm is not None
        return [('scalac', compiler), ('java', vm)]

    @classmethod
    def autoconfig(cls) -> AutoConfigOutput:
        result: AutoConfigResult = {}

        for key, files in {'scalac': ['scalac'], 'scala': ['scala']}.items():
            file = cls.find_command_from_list(files)
            if file is None:
                return result, False, f'Failed to find "{key}"', ''
            result[key] = file

        scala = result.pop('scala')
        with open(os.devnull, 'w') as devnull:
            process = subprocess.Popen(
                ['bash', '-x', scala, '-usebootcp', '-version'], stdout=devnull, stderr=subprocess.PIPE
            )
        output = utf8text(process.communicate()[1])
        log = [i for i in output.split('\n') if 'scala.tools.nsc.MainGenericRunner' in i]

        if not log:
            return result, False, f'Failed to parse: {scala}', ''

        cmdline = log[-1].lstrip('+ ').split()
        vm = cls.find_command_from_list([cmdline[0]])
        if not vm:
            return result, False, f'Failed to find: {cmdline[0]}', ''

        result['scala_vm'] = cls.unravel_java(vm)
        result['scala_args'] = [i for i in cmdline[1:-1] if not i.startswith(('-Xmx', '-Xms'))]

        data = cls.autoconfig_run_test(result)
        if data[1]:
            data = data[:2] + (f'Using {scala}',) + data[3:]
        return data
