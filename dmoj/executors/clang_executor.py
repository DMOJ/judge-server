from .gcc_executor import GCCExecutor


class ClangExecutor(GCCExecutor):
    arch = 'clang_target_arch'

    @classmethod
    def get_version_flags(cls, command):
        return ['--version']
