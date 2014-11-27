package ca.dmoj.java;

public class ShockerThread extends Thread {
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
            // And kill the submission
            target.stop(JavaSafeExecutor.TLE); // We use our own exception here!
        } catch (ThreadDeath ouch) {
        } catch (InterruptedException ignored) {
        }
    }
}
