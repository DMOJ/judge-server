package ca.dmoj.java;

import java.io.*;
import java.lang.instrument.ClassFileTransformer;
import java.lang.instrument.IllegalClassFormatException;
import java.lang.instrument.Instrumentation;
import java.security.ProtectionDomain;

public class SubmissionAgent {
    private static final String UNCAUGHT_EXCEPTION_UUID = "d4519cd6-6270-4bbb-a040-9bf4bcbd5938";
    private static Throwable lastError;

    public static void premain(String argv, Instrumentation inst) throws UnsupportedEncodingException {
        boolean unicode = false;
        boolean noBigInt = false;
        String policy = null;
        if (argv != null)
            for (String opt : argv.split(",")) {
                opt = opt.toLowerCase();
                if (opt.equals("unicode")) unicode = true;
                if (opt.equals("nobiginteger")) noBigInt = true;
                if (opt.startsWith("policy:")) policy = opt.split(":")[1];
            }

        if (policy == null) throw new IllegalStateException("must specify policy file");

        final Thread selfThread = Thread.currentThread();

        if (noBigInt)
            inst.addTransformer(new ClassFileTransformer() {
                @Override
                public byte[] transform(ClassLoader loader, String className, Class<?> classBeingRedefined, ProtectionDomain protectionDomain, byte[] classfileBuffer) throws IllegalClassFormatException {
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

        // Swap System.out for a faster alternative.
        // Requires setIO and writeFileDescriptor permissions
        System.setOut(new UnsafePrintStream(new FileOutputStream(FileDescriptor.out), unicode));

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
                if (lastError != null) {
                    System.err.println(UNCAUGHT_EXCEPTION_UUID + ":" + lastError.getClass().getName());
                    System.err.flush();
                }
            }
        }));

        // Set security policy here so that we don't need to grant submissions addShutdownHook, setIO and writeFileDescriptor
        // to all user submissions.
        System.setProperty("java.security.policy", policy);
        System.setSecurityManager(new SecurityManager());
    }
}
