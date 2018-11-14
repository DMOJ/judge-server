from dmoj.executors.CPP11 import Executor as CPP11Executor


class Executor(CPP11Executor):
    command = 'clang++'
    command_paths = ['clang++-%s' % i for i in ['3.9', '3.8', '3.7', '3.6', '3.5', '6.0']] + ['clang++']
    name = 'CLANG++'
    arch = 'clang_target_arch'
