package ca.dmoj.java;

import java.io.*;
import java.lang.instrument.ClassFileTransformer;
import java.lang.instrument.IllegalClassFormatException;
import java.lang.instrument.Instrumentation;
import java.security.ProtectionDomain;

public class SubmissionAgent {
    private static Throwable lastError;

    public static void premain(String argv, Instrumentation inst) throws UnsupportedEncodingException {
        boolean unicode = false;
        boolean noBigInt = false;
        String policy = null;
        if (argv != null)
            for (String opt : argv.split(",")) {
                if (opt.equals("unicode")) unicode = true;
                if (opt.equals("nobiginteger")) noBigInt = true;

                // Split on "policy:" so that paths like R:/tmp/security.policy don't get processed incorrectly
                if (opt.startsWith("policy:")) policy = opt.split("policy:")[1];
            }

        if (policy == null) throw new IllegalStateException("must specify policy file");
        if (!new File(policy).exists()) throw new IllegalStateException("policy file does not exist: " + policy);

        final Thread selfThread = Thread.currentThread();

        if (noBigInt)
            inst.addTransformer(new ClassFileTransformer() {
                @Override
                public byte[] transform(ClassLoader loader, String className, Class<?> classBeingRedefined,
                                        ProtectionDomain protectionDomain, byte[] classfileBuffer)
                                        throws IllegalClassFormatException {
                    // If the class ever loaded it's because a submission used it
                    if (className.equals("java/math/BigInteger")) {
                        // Python side detects fatal exception by checking last stacktrace when error code is nonzero
                        // This will trick the site into displaying "ca.dmoj.java.BigIntegerDisallowedForProblemException"
                        // in the judge message field.
                        selfThread.getUncaughtExceptionHandler()
                                .uncaughtException(selfThread, new BigIntegerDisallowedForProblemException());
                    }

                    // Don't actually retransform anything
                    return classfileBuffer;
                }
            });

        // System.console() is not-null if both the input and output streams are connected to a terminal. Specifically,
        // > isatty(fileno(stdin)) && isatty(fileno(stdout))
        // If we are connected to a pty, it's because we're doing interactive grading - we shouldn't be buffering
        // our output in that case.
        // See <https://github.com/DMOJ/judge/issues/28>
        // Both branches require the setIO and writeFileDescriptor permissions.
        if (System.console() == null)
            // Swap System.out for a faster alternative.
            System.setOut(new UnsafePrintStream(new FileOutputStream(FileDescriptor.out), unicode));
        else
            // Create output PrintStream set to autoflush:
            // > the output buffer will be flushed whenever a byte array is written, one of the println
            // > methods is invoked, or a newline character or byte ('\n') is written
            // This should be sufficient for interactive problems.
            System.setOut(new PrintStream(new FileOutputStream(FileDescriptor.out), true));

        selfThread.setUncaughtExceptionHandler(new Thread.UncaughtExceptionHandler() {
            @Override
            public void uncaughtException(Thread t, Throwable e) {
                lastError = e;
                System.exit(1);
            }
        });

        // UnsafePrintStream buffers heavily, so we must make sure to flush it at the end of execution.
        // Requires addShutdownHook permission
        Runtime.getRuntime().addShutdownHook(new Thread(new Runnable() {
            @Override
            public void run() {
                System.out.flush();
                System.err.flush();

                try {
                    PrintStream state = new PrintStream(new BufferedOutputStream(new FileOutputStream("state")));
                    if (lastError != null) {
                        state.println(lastError.getClass().getName());
                    } else {
                        // End with ! in the event that some sketchy user-defined exception is ever called OK;
                        // ! is an invalid character in class names.
                        state.println("OK!");
                    }
                    state.close();
                } catch (FileNotFoundException ignored) {
                    // state file won't not exist, "abnormal termination" on the Python side
                }
            }
        }));

        // Set security policy here so that we don't need to grant submissions addShutdownHook, setIO and
        // writeFileDescriptor to all user submissions.
        System.setProperty("java.security.policy", policy);
        System.setSecurityManager(new SecurityManager());
    }
}
