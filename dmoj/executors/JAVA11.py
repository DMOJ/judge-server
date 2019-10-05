from dmoj.executors.java_executor import JavacExecutor


class Executor(JavacExecutor):
    compiler = 'javac11'
    vm = 'java11'
    name = 'JAVA11'
    jvm_regex = r'java-11-|openjdk11'

    test_program = '''\
import java.io.IOException;

interface IORunnable {
    public void run() throws IOException;
}

public class self_test {
    public static void run(IORunnable target) throws IOException {
        target.run();
    }

    public static void main(String[] args) throws IOException {
        run(() -> {
            System.out.print("    ".strip());

            var buffer = new byte[4096];
            int read;
            while ((read = System.in.read(buffer)) >= 0)
                System.out.write(buffer, 0, read);
        });
    }
}'''

    def get_compile_args(self):
        return [self.get_compiler(), '-encoding', 'UTF-8', self._code]
