from dmoj.executors.script_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = 'txt'
    name = 'TEXT'
    command = 'cat'
    test_program = 'echo: Hello, World!\n'
    syscalls = ['fadvise64_64', 'fadvise64', 'posix_fadvise', 'arm_fadvise64_64']
