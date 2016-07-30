from .base_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = '.sed'
    name = 'SED'
    command = 'sed'
    command_paths = ['sed']
    test_program = '''s/.*/echo: Hello, World!/
q'''
    syscalls = ['statfs64', 'statfs']
    fs = ['/proc/filesystems$']

    def get_cmdline(self):
        return [self.get_command(), '-f', self._code]

    @classmethod
    def get_command(cls):
        return cls.runtime_dict.get('sed', '/bin/sed')

    @classmethod
    def get_version_flags(cls, command):
        return ['--version']
