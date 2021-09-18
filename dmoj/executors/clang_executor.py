from typing import List

from .gcc_executor import GCCExecutor, MAX_ERRORS


class ClangExecutor(GCCExecutor):
    arch = 'clang_target_arch'

    def get_flags(self) -> List[str]:
        return self.flags + [f'-ferror-limit={MAX_ERRORS}']

    @classmethod
    def get_version_flags(cls, command: str) -> List[str]:
        return ['--version']
