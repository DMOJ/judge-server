import os
import subprocess

from six import iteritems

from dmoj.executors.java_executor import JavaExecutor
from dmoj.utils.unicode import utf8text

with open(os.path.join(os.path.dirname(__file__), 'groovy-security.policy')) as policy_file:
    policy = policy_file.read()


class Executor(JavaExecutor):
    name = 'GROOVY'
    ext = '.groovy'

    compiler = 'groovyc'
    vm = 'groovy_vm'
    security_policy = policy

    test_program = '''\
println System.in.newReader().readLine()
'''

    def create_files(self, problem_id, source_code, *args, **kwargs):
        super(Executor, self).create_files(problem_id, source_code, *args, **kwargs)
        self._class_name = problem_id

    def get_cmdline(self):
        res = super(Executor, self).get_cmdline()

        res[-2:-1] = ['-Dsubmission.file=%s' % self._class_name] + self.runtime_dict['groovy_args']
        return res

    def get_compile_args(self):
        return [self.get_compiler(), self._code]

    @classmethod
    def get_versionable_commands(cls):
        return [('groovyc', cls.get_compiler()), ('java', cls.get_vm())]

    @classmethod
    def autoconfig(cls):
        result = {}

        for key, files in iteritems({'groovyc': ['groovyc'], 'groovy': ['groovy']}):
            file = cls.find_command_from_list(files)
            if file is None:
                return result, False, 'Failed to find "%s"' % key
            result[key] = file

        groovy = result.pop('groovy')
        with open(os.devnull, 'w') as devnull:
            process = subprocess.Popen(['bash', '-x', groovy, '-version'], stdout=devnull, stderr=subprocess.PIPE)
        output = utf8text(process.communicate()[1])
        log = [i for i in output.split('\n') if 'org.codehaus.groovy.tools.GroovyStarter' in i]

        if not log:
            return result, False, 'Failed to parse: %s' % groovy

        cmdline = log[-1].lstrip('+ ').split()

        result['groovy_vm'] = cls.unravel_java(cls.find_command_from_list([cmdline[1]]))
        result['groovy_args'] = [i for i in cmdline[2:-1]]

        data = cls.autoconfig_run_test(result)
        if data[1]:
            data = data[:2] + ('Using %s' % groovy,) + data[3:]
        return data
