from .base_executor import ScriptExecutor
from dmoj.cptbox.handlers import ACCESS_DENIED


class Executor(ScriptExecutor):
    ext = '.pike'
    name = 'PIKE'
    command = 'pike'
    syscalls = ['epoll_create', 'epoll_ctl', ('fstatfs', ACCESS_DENIED),  # Linux
                'socketpair', ('fpathconf', ACCESS_DENIED)]               # FreeBSD
    test_program = '''\
int main() {
    write(Stdio.stdin.gets());
    return 0;
}
'''
