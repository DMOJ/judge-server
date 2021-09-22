from dmoj.executors.CPP11 import Executor as CPP11Executor
from dmoj.executors.clang_executor import CLANG_VERSIONS, ClangExecutor


class Executor(ClangExecutor, CPP11Executor):
    command = 'clang++'
    command_paths = [f'clang++-{i}' for i in CLANG_VERSIONS] + ['clang++']
    name = 'CLANG++'
