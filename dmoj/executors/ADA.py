from dmoj.judgeenv import env
from .GCCExecutor import GCCExecutor


class Executor(GCCExecutor):
    name = 'ADA'
    command = env['runtime'].get('gnatmake')
    ext = '.adb'
    test_program = '''\
with Ada.Text_IO; use Ada.Text_IO;
procedure Hello is
begin
  Put_Line ("echo: Hello, World!");
end Hello;
'''

initialize = Executor.initialize
