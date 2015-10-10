from .java_executor import JavacExecutor
from judgeenv import env


class Executor(JavacExecutor):
    compiler = env['runtime'].get('javac')
    vm = env['runtime'].get('java')
    test_program = '''\
public class self_test {
    public static void main(String[] args) throws java.io.IOException {
        byte[] buffer = new byte[4096];
        int read;
        while ((read = System.in.read(buffer)) >= 0)
            System.out.write(buffer, 0, read);
    }
}'''


initialize = Executor.initialize
