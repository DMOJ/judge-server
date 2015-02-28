import os

from .JAVA import Executor as JavaExecutor
from executors.utils import test_executor
from judgeenv import env


class Executor(JavaExecutor):
    JAVA = 'java8'
    JAVAC = 'javac8'


def initialize():
    if 'java8' not in env['runtime']:
        return False
    if not os.path.isfile(env['runtime']['java8']):
        return False
    return test_executor('JAVA8', Executor, '''\
public class self_test {
    public static void run(Runnable target) {
        target.run();
    }

    public static void main(String[] args) {
        run(() -> System.out.println("Hello, World!"));
    }
}
''', problem='self_test')
