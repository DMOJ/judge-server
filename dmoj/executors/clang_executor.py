from .gcc_executor import GCCExecutor, MAX_ERRORS


class ClangExecutor(GCCExecutor):
    arch = 'clang_target_arch'

    def get_flags(self):
        return self.flags + ['-ferror-limit=%d' % MAX_ERRORS]

    @classmethod
    def get_version_flags(cls, command):
        return ['--version']
