from .java_executor import JavacExecutor
from judgeenv import env


class Executor(JavacExecutor):
    compiler = env['runtime'].get('javac')
    vm = env['runtime'].get('java')

    test_program = '''\
import java.io.IOException;
import java.util.Scanner;

public class self_test {
    public static void main(String[] args) {
        Runnable test = () -> {
            Scanner in = new Scanner(System.in);
            System.out.println(in.nextLine());
        };
        test.run();
    }
}'''


initialize = Executor.initialize
