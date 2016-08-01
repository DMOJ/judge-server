import os.path

from dmoj.executors.java_executor import JavaExecutor

with open(os.path.join(os.path.dirname(__file__), 'java-security.policy')) as policy_file:
    policy = policy_file.read()


class Executor(JavaExecutor):
    name = 'KOTLIN'
    ext = '.kt'

    compiler = 'kotlinc'
    vm = 'kotlin_vm'
    security_policy = policy

    test_program = '''\
fun main(args: Array<String>) {
    println(readLine())
}
'''

    def create_files(self, problem_id, source_code, *args, **kwargs):
        super(Executor, self).create_files(problem_id, source_code, *args, **kwargs)
        self._jar_name = '%s.jar' % problem_id

    def get_cmdline(self):
        res = super(Executor, self).get_cmdline()
        res[-2:] = ['-jar', self._jar_name]
        return res

    def get_compile_args(self):
        return [self.get_compiler(), '-include-runtime', '-d', self._jar_name, self._code]

    @classmethod
    def get_versionable_commands(cls):
        return [('kotlinc', cls.get_compiler()), ('java', cls.get_vm())]
