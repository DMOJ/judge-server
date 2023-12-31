from typing import List

from dmoj.executors.base_executor import VersionFlags
from dmoj.executors.c_like_executor import CLikeExecutor, GCCMixin


class Executor(GCCMixin, CLikeExecutor):
    command = 'gnatmake'
    ext = 'adb'
    test_program = """\
with Ada.Text_IO; use Ada.Text_IO;
procedure Hello is
begin
  Put_Line ("echo: Hello, World!");
end Hello;
"""

    @classmethod
    def get_version_flags(cls, command: str) -> List[VersionFlags]:
        return ['--version']
