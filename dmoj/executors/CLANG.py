from dmoj.executors.C import Executor as CExecutor
from dmoj.executors.clang_executor import ClangExecutor


class Executor(ClangExecutor, CExecutor):
    command = 'clang'
    command_paths = ['clang-%s' % i for i in ['3.9', '3.8', '3.7', '3.6', '3.5']] + ['clang']
