import java.io.*;
import java.lang.management.ManagementFactory;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.net.MalformedURLException;
import java.net.URL;
import java.net.URLClassLoader;
import java.security.AccessControlException;
import java.security.Permission;
import java.util.PropertyPermission;
import java.util.Scanner;

public class JavaSafeExecutor {
    private static ThreadDeath TLE = new ThreadDeath();
    private static int INVOCATION_ERROR_CODE = -1000;
    private static int ACCESS_ERROR_CODE = -1001;
    private static int NO_ENTRY_POINT_ERROR_CODE = -1002;
    private static int PROGRAM_ERROR_CODE = -1;
    private static ShockerThread shockerThread;
    private static ProcessExecutionThread submissionThread;
    private static boolean _safeBlock = false;

    static {
        new Scanner(new ByteArrayInputStream(new byte[128])).close(); // Load locale
    }

    public static void main(String[] argv) throws MalformedURLException, ClassNotFoundException, UnsupportedEncodingException {
        String path = argv[0];
        String classname = argv[1];
        int TL = Integer.parseInt(argv[2]);

        System.setOut(new UnsafePrintStream(new FileOutputStream(java.io.FileDescriptor.out)));

        URLClassLoader classLoader = URLClassLoader.newInstance(new URL[]{new File(path).toURI().toURL()});
        Class program = classLoader.loadClass(classname);
        submissionThread = new ProcessExecutionThread(program);

        // Count runtime loading as part of time used
        // Note that time here might be negative if RT loading time was greater than TL
        // Oh well.
        TL -= ManagementFactory.getRuntimeMXBean().getUptime();

        shockerThread = new ShockerThread(TL, submissionThread);
        System.setSecurityManager(new _SecurityManager());
        shockerThread.start();
        submissionThread.start();

        try {
            submissionThread.join();
        } catch (InterruptedException ignored) {
        }
        _safeBlock = true;
        shockerThread.stop();
        System.out.flush();

        long totalProgramTime = ManagementFactory.getRuntimeMXBean().getUptime();
        boolean tle = submissionThread.tle;

        long mem = -1;
        try {
            BufferedReader in = new BufferedReader(new InputStreamReader(new FileInputStream(new File("/proc/self/status"))));
            for (String line; (line = in.readLine()) != null; ) {
                if (line.startsWith("VmHWM:")) {
                    String[] data = line.split("\\s+");
                    mem = Integer.parseInt(data[1]);
                }
            }
        } catch (Exception ignored) {
        }
        boolean mle = submissionThread.mle;
        int error = submissionThread.error;

        System.err.println();
        System.err.printf("%d %d %d %d %d\n", totalProgramTime, tle ? 1 : 0, mem, mle ? 1 : 0, error);
    }

    public static class _SecurityManager extends SecurityManager {
        @Override
        public void checkPermission(Permission perm) {
            if (perm instanceof RuntimePermission) {
                if (perm.getName().equals("writeFileDescriptor") || perm.getName().equals("readFileDescriptor"))
                    return;
            }
            if (perm instanceof PropertyPermission) {
                if (perm.getActions().contains("write"))
                    throw new AccessControlException(perm.getClass() + " - " + perm.getName() + ": " + perm.getActions(), perm);
                return;
            }
            if (!_safeBlock) {
                throw new AccessControlException(perm.getClass() + " - " + perm.getName() + ": " + perm.getActions(), perm);
            }
        }
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
                _safeBlock = true;
                target.stop(TLE);
            } catch (InterruptedException ignored) {
            }
        }
    }

    public static class ProcessExecutionThread extends Thread {
        private final Class process;
        private boolean tle = false;
        private boolean mle = false;
        private int error = 0;

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
                    } else if (e.getCause() instanceof OutOfMemoryError) {
                        mle = true;
                        return;
                    } else {
                        e.getCause().printStackTrace();
                        error = INVOCATION_ERROR_CODE;
                    }
                } catch (IllegalAccessException e) {
                    e.printStackTrace();
                    error = ACCESS_ERROR_CODE;
                } catch (Throwable throwable) {
                    error = PROGRAM_ERROR_CODE;
                }
            } catch (NoSuchMethodException e) {
                e.printStackTrace();
                error = NO_ENTRY_POINT_ERROR_CODE;
            }
            _safeBlock = true;
            shockerThread.stop();
        }
    }

    public static class UnsafePrintStream extends PrintStream {
        private BufferedWriter acc;

        public UnsafePrintStream(OutputStream out) throws UnsupportedEncodingException {
            super(new ByteArrayOutputStream());
            acc = new BufferedWriter(new OutputStreamWriter(out, "ASCII"), 4096);
        }

        @Override
        public void flush() {
            super.flush();
            try {
                acc.flush();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }

        public void write(int b) {
            try {
                acc.write(b);
            } catch (IOException e) {
                e.printStackTrace();
            }
        }

        public void write(byte buf[], int off, int len) {
            super.write(buf, off, len); // TODO
        }

        private void write(char buf[]) {
            try {
                acc.write(buf);
            } catch (IOException e) {
                e.printStackTrace();
            }
        }

        private void write(String s) {
            try {
                acc.write(s);
            } catch (IOException e) {
                e.printStackTrace();
            }
        }

        private void newLine() {
            try {
                acc.write('\n');
            } catch (IOException e) {
                e.printStackTrace();
            }
        }

        public void print(boolean b) {
            write(b ? "true" : "false");
        }

        public void print(char c) {
            write(String.valueOf(c));
        }

        public void print(int i) {
            write(String.valueOf(i));
        }

        public void print(long l) {
            write(String.valueOf(l));
        }

        public void print(float f) {
            write(String.valueOf(f));
        }

        public void print(double d) {
            write(String.valueOf(d));
        }

        public void print(char s[]) {
            write(s);
        }

        public void print(String s) {
            write(s == null ? "null" : s);
        }

        public void print(Object obj) {
            write(String.valueOf(obj));
        }

        public void println() {
            newLine();
        }

        public void println(boolean x) {
            print(x);
            newLine();
        }

        public void println(char x) {
            print(x);
            newLine();
        }

        public void println(int x) {
            print(x);
            newLine();
        }

        public void println(long x) {
            print(x);
            newLine();
        }

        public void println(float x) {
            print(x);
            newLine();
        }

        public void println(double x) {
            print(x);
            newLine();
        }

        public void println(char x[]) {
            print(x);
            newLine();
        }

        public void println(String x) {
            print(x);
            newLine();
        }

        public void println(Object x) {
            print(String.valueOf(x));
            newLine();
        }
    }
}
