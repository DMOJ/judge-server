from typing import List

from dmoj.executors.base_executor import VersionFlags
from .gcc_executor import GCCExecutor, MAX_ERRORS

CLANG_VERSIONS: List[str] = ['3.9', '3.8', '3.7', '3.6', '3.5']


class ClangExecutor(GCCExecutor):
    arch = 'clang_target_arch'

    def get_flags(self) -> List[str]:
        return self.flags + [f'-ferror-limit={MAX_ERRORS}']

    @classmethod
    def get_version_flags(cls, command: str) -> List[VersionFlags]:
        return ['--version']
