from dmoj.executors.java_executor import JavacExecutor


class Executor(JavacExecutor):
    compiler = 'javac'
    vm = 'java'
    name = 'JAVA7'
    jvm_regex = r'java-7-|openjdk7'

    test_program = '''\
public class self_test {
    public static void main(String[] args) throws java.io.IOException {
        byte[] buffer = new byte[4096];
        int read;
        while ((read = System.in.read(buffer)) >= 0)
            System.out.write(buffer, 0, read);
    }
}'''
