from .gcc_executor import GCCExecutor


class Executor(GCCExecutor):
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
    def get_version_flags(cls, command):
        return ['--version']
