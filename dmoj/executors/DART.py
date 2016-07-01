from .base_executor import ScriptExecutor
from dmoj.judgeenv import env


class Executor(ScriptExecutor):
    ext = '.dart'
    name = 'DART'
    nproc = 50
    command = env['runtime'].get('dart')
    test_program = '''
void main() {
    print("echo: Hello, World!");
}
'''
    address_grace = 786432

    syscalls = ['epoll_create', 'epoll_ctl']
    fs = ['.*\.(so|dart)', '/proc/meminfo$', '/dev/urandom$']
