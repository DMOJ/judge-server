import java.io.*;
import java.lang.management.ManagementFactory;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.net.MalformedURLException;
import java.net.URL;
import java.net.URLClassLoader;

public class JavaSafeExecutor {
    private static ThreadDeath TLE = new ThreadDeath();
    private static PrintStream STDERR = System.err;
    private static int INVOCATION_ERROR_CODE = -1000;
    private static int ACCESS_ERROR_CODE = -1001;
    private static int NO_ENTRY_POINT_ERROR_CODE = -1002;
    private static int PROGRAM_ERROR_CODE = -1;
    private static ShockerThread shockerThread;
    private static ProcessExecutionThread submissionThread;

    public static void main(String[] argv) throws MalformedURLException, ClassNotFoundException {
        String path = argv[0];
        String classname = argv[1];
        int timelimit = Integer.parseInt(argv[2]);

        System.setErr(System.out);

        URLClassLoader classLoader = URLClassLoader.newInstance(new URL[]{new File(path).toURI().toURL()});
        Class program = classLoader.loadClass(classname);
        submissionThread = new ProcessExecutionThread(program);

        // Count runtime loading as part of time used
        timelimit -= ManagementFactory.getRuntimeMXBean().getUptime();

        shockerThread = new ShockerThread(timelimit, submissionThread);
        shockerThread.start();

        submissionThread.start();

        try {
            submissionThread.join();
        } catch (InterruptedException ignored) {
        }

        long totalProgramTime = ManagementFactory.getRuntimeMXBean().getUptime();
        boolean tle = submissionThread.tle;

        long mem = -1;
        try {
            BufferedReader in = new BufferedReader(new InputStreamReader(new FileInputStream(new File("/proc/self/status"))));
            for (String line; (line = in.readLine()) != null; ) {
                if (line.startsWith("VmHWM:")) {
                    String[] data = line.split(" ");
                    mem = Integer.parseInt(data[1]);
                }
            }
        } catch (IOException ignored) {
        }
        STDERR.printf("%d %d %d\n", totalProgramTime, tle ? 1 : 0, mem);
    }

    public static class ShockerThread extends Thread {
        private final long timelimit;
        private final Thread target;

        public ShockerThread(long timelimit, Thread target) {
            this.timelimit = timelimit;
            this.target = target;
        }

        @Override
        public void run() {
            try {
                Thread.sleep(timelimit);
                target.stop(TLE);
            } catch (InterruptedException ignored) {
            }
        }
    }

    public static class ProcessExecutionThread extends Thread {
        private final Class process;
        private boolean tle = false;

        public ProcessExecutionThread(Class process) {
            this.process = process;
        }

        @Override
        public void run() {
            Method handle;
            try {
                handle = process.getMethod("main", String[].class);
                if (!Modifier.isStatic(handle.getModifiers())) System.exit(-10);
                try {
                    handle.invoke(null, new Object[]{new String[0]});
                } catch (InvocationTargetException e) {
                    if (e.getCause() == TLE) {
                        tle = true;
                        return;
                    }
                    e.printStackTrace(STDERR);
                    System.exit(INVOCATION_ERROR_CODE);
                } catch (IllegalAccessException e) {
                    e.printStackTrace(STDERR);
                    System.exit(ACCESS_ERROR_CODE);
                } catch (Throwable throwable) {
                    System.exit(PROGRAM_ERROR_CODE);
                }
            } catch (NoSuchMethodException e) {
                e.printStackTrace(STDERR);
                System.exit(NO_ENTRY_POINT_ERROR_CODE);
            }
            shockerThread.stop();
        }
    }
}
