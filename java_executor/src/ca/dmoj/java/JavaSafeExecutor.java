package ca.dmoj.java;

import java.io.*;
import java.net.MalformedURLException;
import java.net.URL;
import java.net.URLClassLoader;
import java.util.Scanner;

import java.util.Arrays;

@SuppressWarnings("deprecation")
public class JavaSafeExecutor {
    /**
     * We use our own instance of ThreadDeath for killing submissions.
     * This is just so that a `throw new ThreadDeath()` directive in a user's submission will not be
     * incorrectly marked as TLE. But who throws ThreadDeaths randomly, anyways?
     */
    public static ThreadDeath TLE = new ThreadDeath();
    /**
     * Used to kill the submission thread when the user calls System.exit.
     */
    public static ThreadDeath EXIT_REQUESTED = new ThreadDeath();
    /**
     * Reflection failed with IllegalAccessException. Did the SecurityManager fail?
     */
    public static int ACCESS_ERROR_CODE = -1001;
    /**
     * The user did not declare a `public static void main(String[] argv)` in their code.
     * How are we supposed to run it?
     */
    public static int NO_ENTRY_POINT_ERROR_CODE = -1002;
    /**
     * User's submission threw a Throwable, which we caught.
     */
    public static int PROGRAM_ERROR_CODE = 1;
    /**
     * Class.forName failed; internal error.
     */
    public static int CLASS_NOT_FOUND_ERROR_CODE = -1003;
    /**
     * Class.forName failed; internal error.
     */
    public static int NO_CLASS_DEF_ERROR_CODE = -1004;
    /**
     * Thread to kill the user's submission after their time limit is exceeded.
     */
    static ShockerThread shockerThread;
    /**
     * The thread the user's submission runs on.
     */
    static SubmissionThread submissionThread;
    static Thread selfThread;
    /**
     * Flag to indicate that the security manager should be deactivated.
     * Should be set to false before running the user's submission, and false after it has finished running.
     * If this flag somehow is set to false while a user's submission is running, the judging server may be
     * compromised: the submission gains the same access level as the user the judge is running under.
     */
    static boolean _safeBlock = false;
    /**
     * The current working directory of the submission, used for classpath adding.
     */
    static String cwd;

    static File statefile;

    static boolean isUnicode = false;

    static long startupTime = 0;
    
    static {
        /*
        Scanner needs to load some locale files before it can be used. Since "files" implies IO which is blocked by
        our security manager, we force Scanner to load the files here, before our security manager is activated.
         */
        new Scanner(new ByteArrayInputStream(new byte[128])).close();
    }

    static void writeState(String state, Object... format) throws IOException {
        FileOutputStream fos = new FileOutputStream(statefile);
        PrintStream out = new PrintStream(fos);
        out.format(state, format);
        fos.close();
    }

    static void printStateAndExit() throws IOException {
        // UnsafePrintStream buffers
        System.out.flush();

        long totalProgramTime = System.nanoTime() - startupTime;
        boolean tle = submissionThread.isTle();

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
        boolean mle = submissionThread.isMle();
        int error = submissionThread.getError();
        Throwable exc = submissionThread.getException();

        writeState("%d %d %d %d %d %s\n", totalProgramTime, tle ? 1 : 0, mem, mle ? 1 : 0, error, exc != null ? exc.getClass().getName() : "OK");
        System.exit(0);
    }

    public static void main(String[] argv) throws MalformedURLException, ClassNotFoundException, UnsupportedEncodingException, IOException {
        cwd = new File(argv[0]).toString(); // Resolve relative paths
        String classname = argv[1];
        int TL = Integer.parseInt(argv[2]);
        selfThread = Thread.currentThread();
        statefile = new File(new File(cwd), argv[3]);

        isUnicode = Arrays.asList(argv).contains("-unicode");

        System.setOut(new UnsafePrintStream(new FileOutputStream(FileDescriptor.out), isUnicode));

        URLClassLoader classLoader = new URLClassLoader(new URL[]{new File(cwd).toURI().toURL()}) {
            private void askShouldFail(String name) throws ClassNotFoundException {
                if (name.startsWith("ca.dmoj.")) throw new ClassNotFoundException("Nope");
            }

            @Override
            public Class<?> loadClass(String name, boolean init) throws ClassNotFoundException {
                askShouldFail(name);
                return super.loadClass(name, init);
            }

            @Override
            protected Class<?> findClass(String name) throws ClassNotFoundException {
                askShouldFail(name);
                return super.findClass(name);
            }
        };
        startupTime = System.nanoTime();
        Class program;
        try {
            program = classLoader.loadClass(classname);
        } catch (ClassNotFoundException e) {
            e.printStackTrace();
            writeState("\n%d %d %d %d %d CNF\n", 0, 0, 0, 0, CLASS_NOT_FOUND_ERROR_CODE);
            return;
        } catch (NoClassDefFoundError ex) {
            ex.printStackTrace();
            writeState("\n%d %d %d %d %d CNF\n", 0, 0, 0, 0, NO_CLASS_DEF_ERROR_CODE);
            return;
        }
        submissionThread = new SubmissionThread(program);

        shockerThread = new ShockerThread(TL, submissionThread);
        System.setSecurityManager(new SubmissionSecurityManager());
        shockerThread.start();
        submissionThread.start();

        try {
            submissionThread.join();
        } catch (InterruptedException ignored) {
        }
        shockerThread.stop();

        printStateAndExit();
    }
}
