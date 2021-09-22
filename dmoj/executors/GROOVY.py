import os
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

from dmoj.executors.base_executor import AutoConfigOutput, AutoConfigResult
from dmoj.executors.java_executor import JavaExecutor
from dmoj.utils.unicode import utf8text


class Executor(JavaExecutor):
    ext = 'groovy'

    compiler = 'groovyc'
    vm = 'groovy_vm'

    test_program = """\
println System.in.newReader().readLine()
"""

    def create_files(self, problem_id: str, source_code: bytes, *args, **kwargs) -> None:
        super().create_files(problem_id, source_code, *args, **kwargs)
        self._class_name = problem_id

    def get_cmdline(self, **kwargs) -> List[str]:
        res = super().get_cmdline(**kwargs)

        res[-2:-1] = self.runtime_dict['groovy_args']
        return res

    def get_compile_args(self):
        compiler = self.get_compiler()
        assert compiler is not None
        assert self._code is not None
        return [compiler, self._code]

    def get_compile_env(self) -> Dict[str, str]:
        vm = self.get_vm()
        assert vm is not None
        return {'JAVA_HOME': str(Path(os.path.realpath(vm)).parent.parent)}

    @classmethod
    def get_versionable_commands(cls) -> List[Tuple[str, str]]:
        compiler = cls.get_compiler()
        vm = cls.get_vm()
        assert compiler is not None
        assert vm is not None
        return [('groovyc', compiler), ('java', vm)]

    @classmethod
    def autoconfig(cls) -> AutoConfigOutput:
        result: AutoConfigResult = {}

        for key, files in {'groovyc': ['groovyc'], 'groovy': ['groovy']}.items():
            file = cls.find_command_from_list(files)
            if file is None:
                return result, False, f'Failed to find "{key}"', ''
            result[key] = file

        groovy = result.pop('groovy')
        with open(os.devnull, 'w') as devnull:
            process = subprocess.Popen(['bash', '-x', groovy, '-version'], stdout=devnull, stderr=subprocess.PIPE)
        output = utf8text(process.communicate()[1])
        log = [i for i in output.split('\n') if 'org.codehaus.groovy.tools.GroovyStarter' in i and '-classpath' in i]

        if not log:
            return result, False, f'Failed to parse: {groovy}', ''

        cmdline = log[-1].lstrip('+ ').split()

        vm = cls.find_command_from_list([cmdline[1]])
        if not vm:
            return result, False, f'Failed to find: {cmdline[1]}', ''

        result['groovy_vm'] = cls.unravel_java(vm)
        i = cmdline.index('-classpath')
        result['groovy_args'] = ['-classpath', f'.:{cmdline[i + 1]}']

        data = cls.autoconfig_run_test(result)
        if data[1]:
            data = data[:2] + (f'Using {groovy}',) + data[3:]
        return data
