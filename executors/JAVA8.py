from .JAVA import Executor as JavaExecutor


class Executor(JavaExecutor):
    JAVA = 'java8'
    JAVAC = 'javac8'
    name = 'JAVA8'
    test_program = '''\
public class self_test {
    public static void run(Runnable target) {
        target.run();
    }

    public static void main(String[] args) {
        run(() -> System.out.println("Hello, World!"));
    }
}
'''

initialize = Executor.initialize