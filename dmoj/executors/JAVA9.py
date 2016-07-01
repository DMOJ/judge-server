from dmoj.executors.java_executor import JavacExecutor
from dmoj.judgeenv import env


class Executor(JavacExecutor):
    compiler = env['runtime'].get('javac9')
    vm = env['runtime'].get('java9')
    name = 'JAVA9'

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
            byte[] buffer = new byte[4096];
            int read;
            while ((read = System.in.read(buffer)) >= 0)
                System.out.write(buffer, 0, read);
        });
    }
}'''

    def get_compile_args(self):
        return [self.get_compiler(), '-profile', 'compact1', self._code]
