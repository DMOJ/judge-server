from .ruby_executor import RubyExecutor


class Executor(RubyExecutor):
    name = 'RUBY2'
    nproc = -1
    command_paths = (['ruby2.%d' % i for i in reversed(range(0, 5))] +
                     ['ruby2%d' % i for i in reversed(range(0, 5))])
    syscalls = ['poll', 'thr_set_name']
    fs = ['/proc/self/loginuid$']
