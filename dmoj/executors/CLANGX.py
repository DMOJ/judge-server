from dmoj.executors.CPP14 import Executor as CPP14Executor
from dmoj.executors.clang_executor import CLANG_VERSIONS, ClangExecutor


class Executor(ClangExecutor, CPP14Executor):
    command = 'clang++'
    command_paths = [f'clang++-{i}' for i in CLANG_VERSIONS] + ['clang++']
