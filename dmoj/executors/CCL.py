from dmoj.executors.base_executor import CompiledExecutor
from dmoj.executors.mixins import ScriptDirectoryMixin


class Executor(ScriptDirectoryMixin, CompiledExecutor):
    ext = '.cl'
    name = 'CCL'
    command = 'ccl'
    syscalls = ['setrlimit']
    nproc = -1
    test_program = '(write-line (read-line))'
    address_grace = 131072

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

    def launch(self, *args, **kwargs):
        self.__memory_limit = kwargs['memory']
        return super(Executor, self).launch(*args, **kwargs)

    def get_compile_args(self):
        return [self.get_command(), '-b', '-n', '-e', self.compile_script, '--', self._code]

    def get_cmdline(self):
        return [self.get_command(), '-R', str((self.__memory_limit + 32768) * 1024),
                '-b', '-n', '-e', self.execute_script, '--', self.problem]

    def get_executable(self):
        return self.get_command()

    def get_fs(self):
        return super(Executor, self).get_fs() + [self.get_command()]
