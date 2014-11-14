import java.io.*;
import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;
import java.lang.management.RuntimeMXBean;
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
    /**
     * We use our own instance of ThreadDeath for killing submissions.
     * This is just so that a `throw new ThreadDeath()` directive in a user's submission will not be
     * incorrectly marked as TLE. But who throws ThreadDeaths randomly, anyways?
     */
    private static ThreadDeath TLE = new ThreadDeath();
    /**
     * Reflection failed with IllegalAccessException. Did the SecurityManager fail?
     */
    private static int ACCESS_ERROR_CODE = -1001;
    /**
     * The user did not declare a `public static void main(String[] argv)` in their code.
     * How are we supposed to run it?
     */
    private static int NO_ENTRY_POINT_ERROR_CODE = -1002;
    /**
     * User's submission threw a Throwable, which we caught.
     */
    private static int PROGRAM_ERROR_CODE = 1;
    /**
     * Class.forName failed; internal error.
     */
    private static int CLASS_NOT_FOUND_ERROR_CODE = -1003;
    /**
     * Class.forName failed; internal error.
     */
    private static int NO_CLASS_DEF_ERROR_CODE = -1004;
    /**
     * Thread to kill the user's submission after their time limit is exceeded.
     */
    private static ShockerThread shockerThread;
    /**
     * The thread the user's submission runs on.
     */
    private static SubmissionThread submissionThread;
    /**
     * Flag to indicate that the security manager should be deactivated.
     * Should be set to false before running the user's submission, and false after it has finished running.
     * If this flag somehow is set to false while a user's submission is running, the judging server is
     * compromised: the submission has root access.
     */
    private static boolean _safeBlock = false;
    /**
     * The current working directory of the submission, used for classpath adding.
     */
    private static String cwd;

    static {
        /*
        Scanner needs to load some locale files before it can be used. Since "files" implies IO which is blocked by
        our security manager, we force Scanner to load the files here, before our security manager is activated.
         */
        new Scanner(new ByteArrayInputStream(new byte[128])).close();
    }

    public static void main(String[] argv) throws MalformedURLException, ClassNotFoundException, UnsupportedEncodingException {
        cwd = new File(argv[0]).toString(); // Resolve relative paths
        String classname = argv[1];
        int TL = Integer.parseInt(argv[2]);

        System.setOut(new UnsafePrintStream(new FileOutputStream(FileDescriptor.out)));

        URLClassLoader classLoader = URLClassLoader.newInstance(new URL[]{new File(cwd).toURI().toURL()});
        Class program;
        try {
            program = classLoader.loadClass(classname);
        } catch (ClassNotFoundException e) {
            e.printStackTrace();
            System.err.printf("\n%d %d %d %d %d CNF\n", 0, 0, 0, 0, CLASS_NOT_FOUND_ERROR_CODE);
            return;
        } catch (NoClassDefFoundError ex) {
            ex.printStackTrace();
            System.err.printf("\n%d %d %d %d %d CNF\n", 0, 0, 0, 0, NO_CLASS_DEF_ERROR_CODE);
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

        /*
         Fetch the memory usage for the submission. This is a Linux-specific task, and will obviously
         fail on any other OS.

         We could periodically poll MemoryMXBean for heap usage etc, but that would require a third thread and would
         not be as accurate.
         */
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
        Throwable exc = submissionThread.exception;

        System.err.println();
        // Python-side executor interface
        System.err.printf("%d %d %d %d %d %s\n", totalProgramTime, tle ? 1 : 0, mem, mle ? 1 : 0, error, exc != null ? exc.getClass().getName() : "OK");
    }

    public static class SubmissionSecurityManager extends SecurityManager {
        @Override
        public void checkPermission(Permission perm) {
            if (_safeBlock) return;
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
                /*
                    Java's Date API requires reflection. Wow.
                    Thankfully this is safe enough, since it doesn't allow a malicious submission
                    to access JavaSafeExecutor fields.
                 */
                if (fname.equals("suppressAccessChecks")) {
                    return;
                }
            }
            if (perm instanceof PropertyPermission) {
                if (perm.getActions().contains("write")) {
                    if (fname.equals("user.timezone")) return; // Date
                    throw new AccessControlException(perm.getClass() + " - " + perm.getName() + ": " + perm.getActions(), perm);
                }
                return;
            }
            throw new AccessControlException(perm.getClass() + " - " + perm.getName() + ": " + perm.getActions(), perm);
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
                // Wait for TL
                Thread.sleep(timelimit);
                // Then disable the security manager
                _safeBlock = true;
                // And kill the submission
                target.stop(TLE); // We use our own exception here!
                // TODO: a submission may do something bad after _safeBlock = true but before the thread is stopped
            } catch (ThreadDeath ouch) {
            } catch (InterruptedException ignored) {
            }
        }
    }

    public static class SubmissionThread extends Thread {
        private final Class submission;
        private boolean tle = false;
        private boolean mle = false;
        private int error = 0;
        private Throwable exception;

        public SubmissionThread(Class process) {
            super(null, null, "Submission-Grading-Thread(" + process.getSimpleName() + ")", 8000000 /* Some pretty large stack size */);
            this.submission = process;
        }

        @Override
        @SuppressWarnings("unchecked")
        public void run() {
            Method handle;
            try {
                handle = submission.getMethod("main", String[].class);
                if (!Modifier.isStatic(handle.getModifiers())) System.exit(NO_ENTRY_POINT_ERROR_CODE);
                try {
                    handle.invoke(null, new Object[]{new String[0]});
                } catch (InvocationTargetException e) {
                    // All program errors will be wrapped in an InvocationTargetException
                    Throwable ex = e.getCause();
                    if (ex == TLE) {
                        // We've caught the ThreadDeath we threw to kill the submission thread in case of TLE.
                        tle = true;
                        return;
                    } else if (ex instanceof OutOfMemoryError) {
                        // TODO: prevent `throw new OutOfMemoryError()` as being counted as MLE
                        mle = true;
                        return;
                    } else {
                        ex.printStackTrace();
                        exception = e.getCause();
                        error = PROGRAM_ERROR_CODE;
                    }
                } catch (IllegalAccessException e) {
                    e.printStackTrace();
                    error = ACCESS_ERROR_CODE;
                } catch (Throwable throwable) {
                    throwable.printStackTrace();
                    exception = throwable.getCause();
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

    /**
     * The regular PrintStream set as System.out is just way too slow.
     * This PrintStream implementation is a couple dozen times faster, at the cost of not being thread-safe.
     * Since we forbid cloning anyways, this is not an issue as only the submission thread will ever print.
     *
     * FIXME: we use the ASCII encoding for speed reasons, but this may (will) cause Java submissions to fail
     * FIXME: problems that require unicode output. Maybe we should have a -unicode flag?
     */
    public static class UnsafePrintStream extends PrintStream {
        private BufferedWriter writer;
        private OutputStreamWriter bin;
        private OutputStream out;
        private boolean trouble;

        public UnsafePrintStream(OutputStream out) throws UnsupportedEncodingException {
            super(new ByteArrayOutputStream());
            this.out = out;
            bin = new OutputStreamWriter(out, "ASCII");
            writer = new BufferedWriter(bin, 4096 /* 4k buffer seems to work pretty well */);
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
