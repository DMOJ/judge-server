package ca.dmoj.java;

import ca.dmoj.java.JavaSafeExecutor;
import ca.dmoj.java.SubmissionThread;

import java.io.IOException;

public class ShockerThread extends Thread {
    private final long timelimit;
    private final SubmissionThread target;
    private boolean terminated = false;

    public ShockerThread(long timelimit, SubmissionThread target) {
        super("Grader-TL-Thread");
        this.timelimit = timelimit;
        this.target = target;
    }

    @Override
    public void run() {
        // Fix for https://github.com/DMOJ/judge/issues/151 - printStateAndExit outside InterruptedException
        // monitoring, otherwise a submission that is able to gain a reference to this object via ThreadGroup
        // is able to interrupt() this Thread and therefore bypass time limit.
        try {
            // Wait for TL
            Thread.sleep(timelimit);
        } catch (ThreadDeath ouch) {
        } catch (InterruptedException ignored) {
        }

        // Don't consider TLE if we're already exiting
        if(terminated) return;

        target.tle = true;

        try {
            JavaSafeExecutor.printStateAndExit();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public void terminate() {
        // Flag as terminated
        // Actually stopping this Thread would require more permissions from the SecurityManager from calling
        // classes, so this is the simplest and safest solution
        terminated = true;
    }
}
