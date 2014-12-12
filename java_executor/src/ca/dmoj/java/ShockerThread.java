package ca.dmoj.java;

import ca.dmoj.java.JavaSafeExecutor;
import ca.dmoj.java.SubmissionThread;

import java.io.IOException;

public class ShockerThread extends Thread {
    private final long timelimit;
    private final SubmissionThread target;

    public ShockerThread(long timelimit, SubmissionThread target) {
        super("Grader-TL-Thread");
        this.timelimit = timelimit;
        this.target = target;
    }

    @Override
    public void run() {
        try {
            // Wait for TL
            Thread.sleep(timelimit);
            target.tle = true;
            JavaSafeExecutor.printStateAndExit();
        } catch (ThreadDeath ouch) {
        } catch (InterruptedException ignored) {
        } catch (IOException wtf) {
        }
    }
}
