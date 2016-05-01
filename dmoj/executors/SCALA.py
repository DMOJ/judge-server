from dmoj.judgeenv import env
from dmoj.executors.java_executor import JavaExecutor


class Executor(JavaExecutor):
    name = 'SCALA'
    ext = '.scala'

    compiler = env['runtime'].get('scalac')
    vm = env['runtime'].get('java')

    # Simply run bash -x $(which scala) and copy all arguments after -Xmx and -Xms
    # and add it as a list in the configuration.
    args = env['runtime'].get('scala_args')

    test_program = '''\
object self_test {
  def main(args: Array[String]) {
    println("echo: Hello, World!")
  }
}
'''

    def create_files(self, problem_id, source_code, *args, **kwargs):
        super(Executor, self).create_files(problem_id, source_code, *args, **kwargs)
        self._class_name = problem_id

    def get_cmdline(self):
        res = super(Executor, self).get_cmdline()
        res[-2:-1] = self.args
        return res

    def get_compile_args(self):
        return [self.get_compiler(), self._code]


initialize = Executor.initialize
