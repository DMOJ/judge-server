from dmoj.executors.C import Executor as CExecutor
from dmoj.executors.clang_executor import CLANG_VERSIONS, ClangExecutor


class Executor(ClangExecutor, CExecutor):
    command = 'clang'
    command_paths = [f'clang-{i}' for i in CLANG_VERSIONS] + ['clang']
    name = 'CLANG'
