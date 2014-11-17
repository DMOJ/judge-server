package ca.dmoj.java;

import java.io.*;

/**
 * The regular PrintStream set as System.out is just way too slow.
 * This PrintStream implementation is a couple dozen times faster, at the cost of not being thread-safe.
 * Since we forbid cloning anyways, this is not an issue as only the submission thread will ever print.
 *
 * FIXME: we use the ASCII encoding for speed reasons, but this may (will) cause Java submissions to fail
 * FIXME: problems that require unicode output. Maybe we should have a -unicode flag?
 */
public class UnsafePrintStream extends PrintStream {
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
