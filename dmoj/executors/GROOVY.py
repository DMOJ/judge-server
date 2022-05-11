import os
import subprocess
from pathlib import Path

from dmoj.executors.java_executor import JavaExecutor
from dmoj.utils.unicode import utf8text


class Executor(JavaExecutor):
    ext = 'groovy'

    compiler = 'groovyc'
    vm = 'groovy_vm'

    test_program = """\
println System.in.newReader().readLine()
"""

    def create_files(self, problem_id, source_code, *args, **kwargs):
        super().create_files(problem_id, source_code, *args, **kwargs)
        self._class_name = problem_id

    def get_cmdline(self, **kwargs):
        res = super().get_cmdline(**kwargs)

        res[-2:-1] = self.runtime_dict['groovy_args']
        return res

    def get_compile_args(self):
        return [self.get_compiler(), self._code]

    def get_compile_env(self):
        return {'JAVA_HOME': str(Path(os.path.realpath(self.get_vm())).parent.parent)}

    @classmethod
    def get_versionable_commands(cls):
        return [('groovyc', cls.get_compiler()), ('java', cls.get_vm())]

    @classmethod
    def autoconfig(cls):
        result = {}

        for key, files in {'groovyc': ['groovyc'], 'groovy': ['groovy']}.items():
            file = cls.find_command_from_list(files)
            if file is None:
                return result, False, 'Failed to find "%s"' % key
            result[key] = file

        groovy = result.pop('groovy')
        with open(os.devnull, 'w') as devnull:
            process = subprocess.Popen(['bash', '-x', groovy, '-version'], stdout=devnull, stderr=subprocess.PIPE)
        output = utf8text(process.communicate()[1])
        log = [i for i in output.split('\n') if 'org.codehaus.groovy.tools.GroovyStarter' in i and '-classpath' in i]

        if not log:
            return result, False, 'Failed to parse: %s' % groovy

        cmdline = log[-1].lstrip('+ ').split()

        result['groovy_vm'] = cls.unravel_java(cls.find_command_from_list([cmdline[1]]))
        i = cmdline.index('-classpath')
        result['groovy_args'] = ['-classpath', f'.:{cmdline[i + 1]}']

        data = cls.autoconfig_run_test(result)
        if data[1]:
            data = data[:2] + ('Using %s' % groovy,) + data[3:]
        return data
