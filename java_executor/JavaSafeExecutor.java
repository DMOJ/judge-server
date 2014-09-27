import sun.reflect.CallerSensitive;
import sun.reflect.Reflection;

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

public class JavaSafeExecutor {
    private static ThreadDeath TLE = new ThreadDeath();
    private static PrintStream STDERR = System.err;
    private static int INVOCATION_ERROR_CODE = -1000;
    private static int ACCESS_ERROR_CODE = -1001;
    private static int NO_ENTRY_POINT_ERROR_CODE = -1002;
    private static int PROGRAM_ERROR_CODE = -1;
    private static ShockerThread shockerThread;
    private static ProcessExecutionThread submissionThread;
    private static boolean _safeBlock = false;

    public static void main(String[] argv) throws MalformedURLException, ClassNotFoundException {
        String path = argv[0];
        String classname = argv[1];
        int TL = Integer.parseInt(argv[2]);

        System.setErr(System.out);

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

        STDERR.printf("%d %d %d %d %d\n", totalProgramTime, tle ? 1 : 0, mem, mle ? 1 : 0, error);
    }

    public static class _SecurityManager extends SecurityManager {
        @Override
        public void checkPermission(Permission perm) {
            if(perm instanceof PropertyPermission) {
                if(perm.getActions().contains("write"))
                    throw new AccessControlException("access denied", perm);
            }
            if (!_safeBlock) {
                throw new AccessControlException("access denied", perm);
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
                    e.printStackTrace(STDERR);
                    error = ACCESS_ERROR_CODE;
                } catch (Throwable throwable) {
                    error = PROGRAM_ERROR_CODE;
                }
            } catch (NoSuchMethodException e) {
                e.printStackTrace(STDERR);
                error = NO_ENTRY_POINT_ERROR_CODE;
            }
            _safeBlock = true;
            shockerThread.stop();
        }
    }
}
