import os
import os.path
import subprocess

from dmoj.executors.java_executor import JavaExecutor

with open(os.path.join(os.path.dirname(__file__), 'kotlin-security.policy')) as policy_file:
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
        self._class_name = '%s%s%sKt' % (['', '_'][problem_id[0] in '0123456789'], problem_id[0].upper(), problem_id[1:])

    def get_cmdline(self):
        res = super(Executor, self).get_cmdline()

        res[-2:-1] = ['-Dsubmission.file=%s' % self._class_name, '-Dsubmission.dir=%s' % os.path.dirname(self._code)] + self.runtime_dict.get('kotlin_args')

        return res

    def get_compile_args(self):
        return [self.get_compiler(), self._code]
