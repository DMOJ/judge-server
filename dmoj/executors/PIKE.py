from dmoj.cptbox.handlers import ACCESS_EACCES
from dmoj.executors.script_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = 'pike'
    command = 'pike'
    syscalls = [
        # Linux
        ('fstatfs', ACCESS_EACCES),
        # FreeBSD
        'socketpair',
        ('fpathconf', ACCESS_EACCES),
    ]
    test_program = """\
int main() {
    write(Stdio.stdin.gets());
    return 0;
}
"""
