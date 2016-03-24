import os
import errno

from error import CompileError
from .java_executor import JavaExecutor, JavaProcess, deunicode, JAVA_SANDBOX
from judgeenv import env


class ScalaProcess(JavaProcess):
    def get_command_line(self, class_name, cwd, memory_limit, time_limit, vm):
        return ['scala', JAVA_SANDBOX, cwd, class_name, str(int(time_limit * 1000)), 'state']

    def get_environ(self, class_name, cwd, java, memory_limit, time_limit, vm):
        env = os.environ.copy()
        env.update({'JAVA_OPTS': '-Xmx%sK -%s' % (memory_limit, vm)})
        return env


class Executor(JavaExecutor):
    name = 'SCALA'
    ext = '.scala'
    compiler = env['runtime'].get('scalac')
    vm = env['runtime'].get('scala')
    process_class = ScalaProcess
    test_program = '''\
object self_test {
  def main(args: Array[String]) {
    println("echo: Hello, World!")
  }
}
'''

    def create_files(self, problem_id, source_code):
        source_code = deunicode(source_code)
        class_name = problem_id
        self._code = self._file('%s.scala' % class_name)
        try:
            with open(self._code, 'wb') as fo:
                fo.write(source_code)
        except IOError as e:
            if e.errno in (errno.ENAMETOOLONG, errno.ENOENT):
                raise CompileError('Why do you need a class name so long? '
                                   'As a judge, I sentence your code to death.')
            raise
        self._class_name = class_name

    def get_compile_args(self):
        return [self.get_compiler(), self._code]

initialize = Executor.initialize
