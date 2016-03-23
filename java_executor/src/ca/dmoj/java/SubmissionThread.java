package ca.dmoj.java;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;

public class SubmissionThread extends Thread {
    private final Class submission;
    boolean tle = false;
    private boolean mle = false;
    private int error = 0;
    private Throwable exception;

    public SubmissionThread(Class process, ThreadGroup group) {
        super(group, null, "Submission-Grading-Thread(" + process.getSimpleName() + ")", 1<<27 /* Some pretty large stack size */);
        this.submission = process;
    }

    @Override
    @SuppressWarnings("unchecked")
    public void run() {
        Method handle;
        try {
            handle = submission.getMethod("main", String[].class);
            if (!Modifier.isStatic(handle.getModifiers())) System.exit(JavaSafeExecutor.NO_ENTRY_POINT_ERROR_CODE);
            try {
                handle.invoke(null, new Object[]{new String[]{"ONLINE_JUDGE"}});
            } catch (InvocationTargetException e) {
                // All program errors will be wrapped in an InvocationTargetException
                Throwable ex = e.getCause();
                ex.printStackTrace();
                if(ex == JavaSafeExecutor.EXIT_REQUESTED) return;
                if (ex == JavaSafeExecutor.TLE) {
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
                    error = JavaSafeExecutor.PROGRAM_ERROR_CODE;
                }
            } catch (IllegalAccessException e) {
                e.printStackTrace();
                error = JavaSafeExecutor.ACCESS_ERROR_CODE;
            } catch(OutOfMemoryError e) {
                // But why do this again if we already check for this case above?
                //              https://github.com/DMOJ/judge/issues/29
                // Future maintainers, if any, enjoy.
                mle = true;
            } catch (Throwable throwable) {
                throwable.printStackTrace();
                exception = throwable.getCause();
                error = JavaSafeExecutor.PROGRAM_ERROR_CODE;
            }
        } catch (NoSuchMethodException e) {
            e.printStackTrace();
            error = JavaSafeExecutor.NO_ENTRY_POINT_ERROR_CODE;
        }
        JavaSafeExecutor.shockerThread.terminate();
    }

    public Class getSubmission() {
        return submission;
    }

    public boolean isTle() {
        return tle;
    }

    public boolean isMle() {
        return mle;
    }

    public int getError() {
        return error;
    }

    public Throwable getException() {
        return exception;
    }
}
