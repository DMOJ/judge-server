from dmoj.cptbox.handlers import ACCESS_EACCES
from dmoj.executors.script_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = 'pike'
    name = 'PIKE'
    command = 'pike'
    syscalls = ['epoll_create', 'epoll_ctl', ('fstatfs', ACCESS_EACCES),  # Linux
                'socketpair', ('fpathconf', ACCESS_EACCES)]               # FreeBSD
    test_program = '''\
int main() {
    write(Stdio.stdin.gets());
    return 0;
}
'''
