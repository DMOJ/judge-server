from .java_executor import JavacExecutor, JavaProcess
from judgeenv import env
import time
import os


class ScalaProcess(JavacExecutor):
    def __init__(self, java, class_name, cwd, time_limit, memory_limit, statefile, vm='client'):
        java_env = os.environ.copy()
        java_env.update({'JAVA_OPTS': '-Xmx%sK' % memory_limit})
        self.process = Popen(['scala', JAVA_EXECUTOR, cwd,
                              class_name, str(int(time_limit * 1000)), 'state'], executable=java, cwd=cwd,
                             stdin=PIPE, stdout=PIPE, stderr=PIPE,
                             env=java_env)
        self.execution_time, self.tle = None, None
        self.max_memory, self.mle = None, None
        self.stderr = None
        self.error_info, self.error = None, None
        self.returncode = None
        self.feedback = None
        self.time_limit = time_limit
        self.memory_limit = memory_limit
        self.statefile = statefile
        self._killed = False
        self._start = time.time()

class Executor(JavacExecutor):
    compiler = env['runtime'].get('scalac')
    vm = env['runtime'].get('scala')
    test_program = '''\
object self_test {
  def main(args: Array[String]) {
    println("echo: Hello, World!")
  }
}
'''

    def launch(self, *args, **kwargs):
        return ScalaProcess(java=self.get_vm(), class_name=self._class_name, cwd=self._dir,
                           time_limit=kwargs.get('time'), memory_limit=kwargs.get('memory'), statefile=self.statefile)



initialize = Executor.initialize
