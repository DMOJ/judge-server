from dmoj.executors.compiled_executor import CompiledExecutor


class Executor(CompiledExecutor):
    ext = 'scm'
    name = 'SCM'
    command = 'chicken-csc'
    command_paths = ['chicken-csc', 'csc']
    test_program = '(import chicken.io) (map print (read-lines))'

    def get_compile_args(self):
        return [self.get_command(), self._code]

    @classmethod
    def get_versionable_commands(cls):
        return (('csc', cls.get_command()),)

    @classmethod
    def get_version_flags(cls, command):
        return ['-version']
