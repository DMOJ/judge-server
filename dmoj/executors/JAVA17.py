from dmoj.executors.java_executor import JavacExecutor


class Executor(JavacExecutor):
    compiler = 'javac17'
    vm = 'java17'
    jvm_regex = r'java-17-|openjdk17'

    test_program = '''\
import java.io.IOException;

sealed interface IORunnableInterface permits IORunnable {
    public void run() throws IOException;
}

final class IORunnable implements IORunnableInterface {
    public void run() throws IOException {
        System.out.print("""

""".strip());

        var buffer = new byte[4096];
        int read;
        while ((read = System.in.read(buffer)) >= 0)
            System.out.write(buffer, 0, read);
    }
}

public class self_test {
    public static void main(String[] args) throws IOException {
        new IORunnable().run();
    }
}'''

    def get_compile_args(self):
        return [self.get_compiler(), '-encoding', 'UTF-8', self._code]
