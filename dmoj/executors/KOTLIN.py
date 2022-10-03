from dmoj.cptbox.filesystem_policies import ExactFile
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

    def create_files(self, problem_id, source_code, *args, **kwargs):
        super().create_files(problem_id, source_code, *args, **kwargs)
        self._jar_name = '%s.jar' % problem_id

    def get_cmdline(self, **kwargs):
        res = super().get_cmdline(**kwargs)
        res[-2:] = ['-jar', self._jar_name]
        return res

    def get_compile_args(self):
        return [self.get_compiler(), '-include-runtime', '-d', self._jar_name, self._code]

    @classmethod
    def get_versionable_commands(cls):
        return [('kotlinc', cls.get_compiler()), ('java', cls.get_vm())]

    @classmethod
    def autoconfig(cls):
        kotlinc = cls.find_command_from_list(['kotlinc'])
        if kotlinc is None:
            return None, False, 'Failed to find "kotlinc"'

        java = cls.find_command_from_list(['java'])
        if java is None:
            return None, False, 'Failed to find "java"'

        return cls.autoconfig_run_test({cls.compiler: kotlinc, cls.vm: cls.unravel_java(java)})
