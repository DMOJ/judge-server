from dmoj.executors.mixins import StripCarriageReturnsMixin
from dmoj.executors.script_executor import ScriptExecutor


# We want to strip carriage returns because the source code is outputted byte-for-byte,
# and we strip these in test data.
class Executor(StripCarriageReturnsMixin, ScriptExecutor):
    ext = 'txt'
    command = 'cat'
    test_program = 'echo: Hello, World!\n'
    syscalls = ['fadvise64_64', 'fadvise64', 'posix_fadvise', 'arm_fadvise64_64']
