import java.io.*;
import java.lang.management.ManagementFactory;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.lang.reflect.ReflectPermission;
import java.net.MalformedURLException;
import java.net.URL;
import java.net.URLClassLoader;
import java.security.AccessControlException;
import java.security.Permission;
import java.util.PropertyPermission;
import java.util.Scanner;

@SuppressWarnings("deprecation")
public class JavaSafeExecutor {
    private static ThreadDeath TLE = new ThreadDeath();
    private static int ACCESS_ERROR_CODE = -1001;
    private static int NO_ENTRY_POINT_ERROR_CODE = -1002;
    private static int PROGRAM_ERROR_CODE = 1;
    private static int CLASS_NOT_FOUND_ERROR_CODE = -1003;
    private static int NO_CLASS_DEF_ERROR_CODE = -1004;
    private static ShockerThread shockerThread;
    private static SubmissionThread submissionThread;
    private static boolean _safeBlock = false;
    private static String cwd;

    static {
        new Scanner(new ByteArrayInputStream(new byte[128])).close(); // Load locale
    }

    public static void main(String[] argv) throws MalformedURLException, ClassNotFoundException, UnsupportedEncodingException {
        cwd = new File(argv[0]).toString(); // Resolve
        String classname = argv[1];
        int TL = Integer.parseInt(argv[2]);

        System.setOut(new UnsafePrintStream(new FileOutputStream(FileDescriptor.out)));

        URLClassLoader classLoader = URLClassLoader.newInstance(new URL[]{new File(cwd).toURI().toURL()});
        Class program;
        try {
            program = classLoader.loadClass(classname);
        } catch (ClassNotFoundException e) {
            e.printStackTrace();
            System.err.printf("\n%d %d %d %d %d\n", 0, 0, 0, 0, CLASS_NOT_FOUND_ERROR_CODE);
            return;
        } catch (NoClassDefFoundError ex) {
            ex.printStackTrace();
            System.err.printf("\n%d %d %d %d %d\n", 0, 0, 0, 0, NO_CLASS_DEF_ERROR_CODE);
            return;
        }
        submissionThread = new SubmissionThread(program);

        // Count runtime loading as part of time used
        // Note that if the time here more than the TL, I will not take it away.
        // If it is negative, the system is slow enough that you are penalized already.
        long uptime = ManagementFactory.getRuntimeMXBean().getUptime();
        if (TL > uptime)
            TL -= uptime;

        shockerThread = new ShockerThread(TL, submissionThread);
        System.setSecurityManager(new SubmissionSecurityManager());
        shockerThread.start();
        submissionThread.start();

        try {
            submissionThread.join();
        } catch (InterruptedException ignored) {
        }
        _safeBlock = true;
        shockerThread.stop();

        // UnsafePrintStream buffers
        System.out.flush();

        long totalProgramTime = ManagementFactory.getRuntimeMXBean().getUptime();
        boolean tle = submissionThread.tle;

        long mem = 0;
        try {
            BufferedReader in = new BufferedReader(new InputStreamReader(new FileInputStream("/proc/self/status")));
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

    public static class SubmissionSecurityManager extends SecurityManager {
        @Override
        public void checkPermission(Permission perm) {
            String fname = perm.getName().replace("\\", "/");
            if (perm instanceof FilePermission) {
                if (perm.getActions().equals("read") &&
                        (fname.startsWith(cwd + File.separator) ||
                                fname.startsWith("/usr/lib/jvm/") ||
                                fname.contains("/jre/lib/zi/")
                        )) // Date
                    return;
            }
            if (perm instanceof RuntimePermission) {
                if (fname.equals("writeFileDescriptor") ||
                        fname.equals("readFileDescriptor") ||
                        fname.equals("fileSystemProvider"))
                    return;
                if (fname.startsWith("accessClassInPackage")) {
                    if (fname.contains("sun.util.resources"))
                        return;
                }
            }
            if (perm instanceof ReflectPermission) {
                if (fname.equals("suppressAccessChecks"))
                    return; // Seems unsafe but needed for the goddamn date api
            }
            if (perm instanceof PropertyPermission) {
                if (perm.getActions().contains("write")) {
                    if (fname.equals("user.timezone")) return; // Date
                    throw new AccessControlException(perm.getClass() + " - " + perm.getName() + ": " + perm.getActions(), perm);
                }
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
            super("Grader-TL-Thread");
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
            } catch (ThreadDeath ignored) {
            }
        }

        public static class SubmissionThread extends Thread {
            private final Class submission;
            private boolean tle = false;
            private boolean mle = false;
            private int error = 0;

            public SubmissionThread(Class process) {
                super(null, null, "Submission-Grading-Thread(" + process.getSimpleName() + ")", 8000000);
                this.submission = process;
            }

            @Override
            @SuppressWarnings("unchecked")
            public void run() {
                Method handle;
                try {
                    handle = submission.getMethod("main", String[].class);
                    if (!Modifier.isStatic(handle.getModifiers())) System.exit(-10);
                    try {
                        handle.invoke(null, new Object[]{new String[0]});
                    } catch (InvocationTargetException e) {
                        if (e.getCause() == TLE) {
                            tle = true;
                            return;
                        } else if (e.getCause() instanceof OutOfMemoryError) {
                            // Prevent throw new OutOfMemoryError from being counted as MLE
//                        if(e.getCause().getStackTrace()[0].getClassName().equals(submission.getSimpleName())) {
//                            error = PROGRAM_ERROR_CODE;
//                            return;
//                        }
                            mle = true;
                            return;
                        } else {
                            e.getCause().printStackTrace();
                            error = PROGRAM_ERROR_CODE;
                        }
                    } catch (IllegalAccessException e) {
                        e.printStackTrace();
                        error = ACCESS_ERROR_CODE;
                    } catch (Throwable throwable) {
                        throwable.printStackTrace();
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
            private BufferedWriter writer;
            private OutputStreamWriter bin;
            private OutputStream out;
            private boolean trouble;

            public UnsafePrintStream(OutputStream out) throws UnsupportedEncodingException {
                super(new ByteArrayOutputStream());
                this.out = out;
                bin = new OutputStreamWriter(out, "ASCII");
                writer = new BufferedWriter(bin, 4096);
            }

            @Override
            public boolean checkError() {
                return trouble;
            }

            @Override
            public void flush() {
                try {
                    writer.flush();
                } catch (IOException e) {
                    trouble = true;
                }
            }

            public void write(int b) {
                try {
                    writer.write(b);
                } catch (IOException e) {
                    trouble = true;
                }
            }

            public void write(byte buf[], int off, int len) {
                flush();
                try {
                    out.write(buf, off, len);
                } catch (IOException e) {
                    trouble = true;
                }
            }

            private void write(char buf[]) {
                try {
                    writer.write(buf);
                } catch (IOException e) {
                    trouble = true;
                }
            }

            private void write(String s) {
                try {
                    writer.write(s);
                } catch (IOException e) {
                    trouble = true;
                }
            }

            private void newLine() {
                try {
                    writer.write('\n');
                } catch (IOException e) {
                    trouble = true;
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
}
