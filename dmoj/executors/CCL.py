from dmoj.executors.base_executor import CompiledExecutor
from dmoj.executors.mixins import ScriptDirectoryMixin


class Executor(ScriptDirectoryMixin, CompiledExecutor):
    ext = '.cl'
    name = 'CCL'
    command = 'ccl'
    command_paths = ['ccl']
    syscalls = ['setrlimit', 'write', 'modify_ldt']
    fs = ['/dev/tty$', '/etc/(?:nsswitch.conf|passwd)$']
    nproc = -1
    test_program = '(write-line (read-line))'
    address_grace = 524288

    compile_script = '''\
(progn
  (compile-file
    (car *unprocessed-command-line-arguments*))
  (ccl::quit))'''

    execute_script = '''\
(progn
  (defvar *main-module*
    (car *unprocessed-command-line-arguments*))
  (setf *unprocessed-command-line-arguments*
    (cdr *unprocessed-command-line-arguments*))
  (load *main-module*)
  (ccl::quit))'''

    execute_script = '''\
(progn
  (load (car *unprocessed-command-line-arguments*))
  (ccl::quit))'''


    def get_compile_args(self):
        return [self.get_command(), '-b', '-n', '-e', self.compile_script, '--', self._code]

    def get_cmdline(self):
        return [self.get_command(), '-b', '-n', '-e', self.execute_script, '--', self.problem]

    def get_executable(self):
        return self.get_command()

    def get_fs(self):
        return super(Executor, self).get_fs() + [self.get_command()]
