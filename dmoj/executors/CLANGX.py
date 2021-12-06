from dmoj.executors.CPP11 import Executor as CPP11Executor
from dmoj.executors.clang_executor import ClangExecutor


class Executor(ClangExecutor, CPP11Executor):
    command = 'clang++'
    command_paths = ['clang++-%s' % i for i in ['3.9', '3.8', '3.7', '3.6', '3.5']] + ['clang++']
