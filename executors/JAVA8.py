from .java_executor import JavacExecutor
from judgeenv import env


class Executor(JavacExecutor):
    compiler = env['runtime'].get('javac8')
    vm = env['runtime'].get('java8')
    name = 'JAVA8'

    test_program = '''\
import java.io.IOException;
import java.util.Scanner;

interface IORunnable {
    public void run() throws IOException;
}

public class self_test {
    public static void run(IORunnable target) throws IOException {
        target.run();
    }

    public static void main(String[] args) throws IOException {
        run(() -> {
            Scanner in = new Scanner(System.in);
            System.out.println(in.nextLine());
        });
    }
}'''


initialize = Executor.initialize
