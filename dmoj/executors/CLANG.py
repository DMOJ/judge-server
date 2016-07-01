from dmoj.executors.C import Executor as CExecutor


class Executor(CExecutor):
    command = 'clang'
    command_paths = ['clang-%s' % i for i in ['3.9', '3.8', '3.7', '3.6', '3.5']] + ['clang']
    name = 'CLANG'
