import java.util.*;
import java.util.regex.*;
import java.io.*;
import java.lang.reflect.*;
import java.text.*;

public class PApplet
{
    private InputStream stream = System.in;
    private byte[] buf = new byte[1024];
    private int curChar, numChars;
    private static NumberFormat int_nf;
    private static int int_nf_digits;
    private static boolean int_nf_commas;
    private static NumberFormat float_nf;
    private static int float_nf_left;
    private static int float_nf_right;
    private static boolean float_nf_commas;
    static final String ERROR_MIN_MAX = "Cannot use min() or max() on an empty array.";
    static final int PERLIN_YWRAPB = 4;
    static final int PERLIN_YWRAP = 16;
    static final int PERLIN_ZWRAPB = 8;
    static final int PERLIN_ZWRAP = 256;
    static final int PERLIN_SIZE = 4095;
    int perlin_octaves = 4;
    float perlin_amp_falloff = 0.5f;
    int perlin_TWOPI;
    int perlin_PI;
    float[] perlin_cosTable;
    float[] perlin;
    Random perlinRandom;
    protected static LinkedHashMap<String, Pattern> matchPatterns;
    protected static final float[] sinLUT = new float[720];
    protected static final float[] cosLUT = new float[720];
    public static final float EPSILON = 1.0E-4f;
    public static final float MAX_FLOAT = Float.MAX_VALUE;
    public static final float MIN_FLOAT = -3.4028235E38f;
    public static final int MAX_INT = Integer.MAX_VALUE;
    public static final int MIN_INT = Integer.MIN_VALUE;
    public static final float PI = 3.1415927f;
    public static final float HALF_PI = 1.5707964f;
    public static final float THIRD_PI = 1.0471976f;
    public static final float QUARTER_PI = 0.7853982f;
    public static final float TWO_PI = 6.2831855f;
    public static final float TAU = 6.2831855f;
    public static final float DEG_TO_RAD = 0.017453292f;
    public static final float RAD_TO_DEG = 57.295776f;
    public static final String WHITESPACE = " \t\n\r\f\u00a0";
    public static final int RGB = 1;
    public static final int ARGB = 2;
    public static final int HSB = 3;
    public static final int ALPHA = 4;
    public static final int TIFF = 0;
    public static final int TARGA = 1;
    public static final int JPEG = 2;
    public static final int GIF = 3;
    public static final int BLUR = 11;
    public static final int GRAY = 12;
    public static final int INVERT = 13;
    public static final int OPAQUE = 14;
    public static final int POSTERIZE = 15;
    public static final int THRESHOLD = 16;
    public static final int ERODE = 17;
    public static final int DILATE = 18;
    public static final int REPLACE = 0;
    public static final int BLEND = 1;
    public static final int ADD = 2;
    public static final int SUBTRACT = 4;
    public static final int LIGHTEST = 8;
    public static final int DARKEST = 16;
    public static final int DIFFERENCE = 32;
    public static final int EXCLUSION = 64;
    public static final int MULTIPLY = 128;
    public static final int SCREEN = 256;
    public static final int OVERLAY = 512;
    public static final int HARD_LIGHT = 1024;
    public static final int SOFT_LIGHT = 2048;
    public static final int DODGE = 4096;
    public static final int BURN = 8192;
    public static final int CHATTER = 0;
    public static final int COMPLAINT = 1;
    public static final int PROBLEM = 2;
    public static final int PROJECTION = 0;
    public static final int MODELVIEW = 1;
    public static final int CUSTOM = 0;
    public static final int ORTHOGRAPHIC = 2;
    public static final int PERSPECTIVE = 3;
    public static final int GROUP = 0;
    public static final int POINT = 2;
    public static final int POINTS = 3;
    public static final int LINE = 4;
    public static final int LINES = 5;
    public static final int LINE_STRIP = 50;
    public static final int LINE_LOOP = 51;
    public static final int TRIANGLE = 8;
    public static final int TRIANGLES = 9;
    public static final int TRIANGLE_STRIP = 10;
    public static final int TRIANGLE_FAN = 11;
    public static final int QUAD = 16;
    public static final int QUADS = 17;
    public static final int QUAD_STRIP = 18;
    public static final int POLYGON = 20;
    public static final int PATH = 21;
    public static final int RECT = 30;
    public static final int ELLIPSE = 31;
    public static final int ARC = 32;
    public static final int SPHERE = 40;
    public static final int BOX = 41;
    public static final int OPEN = 1;
    public static final int CLOSE = 2;
    public static final int CORNER = 0;
    public static final int CORNERS = 1;
    public static final int RADIUS = 2;
    public static final int CENTER = 3;
    public static final int DIAMETER = 3;
    public static final int CHORD = 2;
    public static final int PIE = 3;
    public static final int BASELINE = 0;
    public static final int TOP = 101;
    public static final int BOTTOM = 102;
    public static final int NORMAL = 1;
    public static final int IMAGE = 2;
    public static final int CLAMP = 0;
    public static final int REPEAT = 1;
    public static final int MODEL = 4;
    public static final int SHAPE = 5;
    public static final int SQUARE = 1;
    public static final int ROUND = 2;
    public static final int PROJECT = 4;
    public static final int MITER = 8;
    public static final int BEVEL = 32;
    public static final int AMBIENT = 0;
    public static final int DIRECTIONAL = 1;
    public static final int SPOT = 3;
    public static final char BACKSPACE = '\b';
    public static final char TAB = '\t';
    public static final char ENTER = '\n';
    public static final char RETURN = '\r';
    public static final char ESC = '\u001b';
    public static final char DELETE = '';
    public static final int CODED = 65535;
    public static final int UP = 38;
    public static final int DOWN = 40;
    public static final int LEFT = 37;
    public static final int RIGHT = 39;
    public static final int ALT = 18;
    public static final int CONTROL = 17;
    public static final int SHIFT = 16;
    public static final int PORTRAIT = 1;
    public static final int LANDSCAPE = 2;
    public static final int SPAN = 0;
    public static final int ARROW = 0;
    public static final int CROSS = 1;
    public static final int HAND = 12;
    public static final int MOVE = 13;
    public static final int TEXT = 2;
    public static final int WAIT = 3;
    @Deprecated
    public static final int ENABLE_NATIVE_FONTS = 1;
    @Deprecated
    public static final int DISABLE_NATIVE_FONTS = -1;
    public static final int DISABLE_DEPTH_TEST = 2;
    public static final int ENABLE_DEPTH_TEST = -2;
    public static final int ENABLE_DEPTH_SORT = 3;
    public static final int DISABLE_DEPTH_SORT = -3;
    public static final int DISABLE_OPENGL_ERRORS = 4;
    public static final int ENABLE_OPENGL_ERRORS = -4;
    public static final int DISABLE_DEPTH_MASK = 5;
    public static final int ENABLE_DEPTH_MASK = -5;
    public static final int DISABLE_OPTIMIZED_STROKE = 6;
    public static final int ENABLE_OPTIMIZED_STROKE = -6;
    public static final int ENABLE_STROKE_PERSPECTIVE = 7;
    public static final int DISABLE_STROKE_PERSPECTIVE = -7;
    public static final int DISABLE_TEXTURE_MIPMAPS = 8;
    public static final int ENABLE_TEXTURE_MIPMAPS = -8;
    public static final int ENABLE_STROKE_PURE = 9;
    public static final int DISABLE_STROKE_PURE = -9;
    public static final int ENABLE_BUFFER_READING = 10;
    public static final int DISABLE_BUFFER_READING = -10;
    public static final int DISABLE_KEY_REPEAT = 11;
    public static final int ENABLE_KEY_REPEAT = -11;
    public static final int DISABLE_ASYNC_SAVEFRAME = 12;
    public static final int ENABLE_ASYNC_SAVEFRAME = -12;
    public static final int HINT_COUNT = 13;
    Random internalRandom;

    /** Custom I/O methods */
    public int readChar()
    {
        try
        {
            if (curChar >= numChars)
            {
                curChar = 0;
                numChars = stream.read(buf);
            }
            if (numChars == -1)
                return numChars;
            return buf[curChar++];
        }
        catch(IOException e)
        {
            throw new Error("Failed to read from IO.");
        }
    }

    private static int fast_pow(int b, int x)
    {
        if (x == 0)
            return 1;
        if (x == 1)
            return b;
        if (x % 2 == 0)
            return fast_pow(b * b, x / 2);
        return b * fast_pow(b * b, x / 2);
    }

    public int readInt()
    {
        int c = readChar(), sgn = 1;
        while (space(c))
            c = readChar();
        if (c == '-')
        {
            sgn = -1;
            c = readChar();
        }
        int res = 0;
        do
        {
            res = (res << 1) + (res << 3);
            res += c - '0';
            c = readChar();
        }
        while (!space(c));
        return res * sgn;
    }

    public String readString()
    {
        int c = readChar();
        while (space(c))
            c = readChar();
        StringBuilder res = new StringBuilder();
        do
        {
            res.appendCodePoint(c);
            c = readChar();
        }
        while (!space(c));
        return res.toString();
    }

    public String readLine()
    {
        int c = readChar();
        while (space(c))
            c = readChar();
        StringBuilder res = new StringBuilder();
        do
        {
            res.appendCodePoint(c);
            c = readChar();
        }
        while (c != '\n');
        return res.toString();
    }

    public double readDouble()
    {
        int c = readChar(), sgn = 1;
        while (space(c))
            c = readChar();
        if (c == '-')
        {
            sgn = -1;
            c = readChar();
        }
        double res = 0;
        while (!space(c) && c != '.')
        {
            if (c == 'e' || c == 'E')
                return res * fast_pow(10, readInt());
            res *= 10;
            res += c - '0';
            c = readChar();
        }

        if (c == '.')
        {
            c = readChar();
            double m = 1;
            while (!space(c))
            {
                if (c == 'e' || c == 'E')
                    return res * fast_pow(10, readInt());
                m /= 10;
                res += (c - '0') * m;
                c = readChar();
            }
        }
        return res * sgn;
    }

    public long readLong()
    {
        int c = readChar(), sgn = 1;
        while (space(c))
            c = readChar();
        if (c == '-')
        {
            sgn = -1;
            c = readChar();
        }
        long res = 0;
        do
        {
            res = (res << 1) + (res << 3);
            res += c - '0';
            c = readChar();
        }
        while (!space(c));
        return res * sgn;
    }

    private boolean space(int c)
    {
        return c == ' ' || c == '\n' || c == '\r' || c == '\t' || c == -1;
    }

    public static void flush()
    {
        System.out.flush();
    }
    /** End custom I/O methods */

public static void print(byte what)
{
    System.out.print(what);
}

public static void print(boolean what)
{
    System.out.print(what);
}

public static void print(char what)
{
    System.out.print(what);
}

public static void print(int what)
{
    System.out.print(what);
}

public static void print(long what)
{
    System.out.print(what);
}

public static void print(float what)
{
    System.out.print(what);
}

public static void print(double what)
{
    System.out.print(what);
}

public static void print(String what)
{
    System.out.print(what);
}

public static /* varargs */ void print(Object... variables)
{
    StringBuilder sb = new StringBuilder();
    for (Object o : variables)
    {
        if (sb.length() != 0)
        {
            sb.append(" ");
        }
        if (o == null)
        {
            sb.append("null");
            continue;
        }
        sb.append(o.toString());
    }
    System.out.print(sb.toString());
}

public static void println()
{
    System.out.println();
}

public static void println(byte what)
{
    System.out.println(what);
}

public static void println(boolean what)
{
    System.out.println(what);
}

public static void println(char what)
{
    System.out.println(what);
}

public static void println(int what)
{
    System.out.println(what);
}

public static void println(long what)
{
    System.out.println(what);
}

public static void println(float what)
{
    System.out.println(what);
}

public static void println(double what)
{
    System.out.println(what);
}

public static void println(String what)
{
    System.out.println(what);
}

public static /* varargs */ void println(Object... variables)
{
    PApplet.print(variables);
    PApplet.println();
}

public static void println(Object what)
{
    if (what == null)
    {
        System.out.println("null");
    }
    else if (what.getClass().isArray())
    {
        PApplet.printArray(what);
    }
    else
    {
        System.out.println(what.toString());
    }
}

public static void printArray(Object what)
{
    block21:
    {
        block22:
        {
            block20:
            {
                if (what != null)
                    break block20;
                System.out.println("null");
                break block21;
            }
            String name = what.getClass().getName();
            if (name.charAt(0) != '[')
                break block22;
            switch (name.charAt(1))
            {
            case '[':
            {
                System.out.println(what);
                break;
            }
            case 'L':
            {
                Object[] poo = (Object[]) what;
                for (int i = 0; i < poo.length; ++i)
                {
                    if (poo[i] instanceof String)
                    {
                        System.out.println("[" + i + "] \"" + poo[i] + "\"");
                        continue;
                    }
                    System.out.println("[" + i + "] " + poo[i]);
                }
                break block21;
            }
            case 'Z':
            {
                boolean[] zz = (boolean[]) what;
                for (int i = 0; i < zz.length; ++i)
                {
                    System.out.println("[" + i + "] " + zz[i]);
                }
                break block21;
            }
            case 'B':
            {
                byte[] bb = (byte[]) what;
                for (int i = 0; i < bb.length; ++i)
                {
                    System.out.println("[" + i + "] " + bb[i]);
                }
                break block21;
            }
            case 'C':
            {
                char[] cc = (char[]) what;
                for (int i = 0; i < cc.length; ++i)
                {
                    System.out.println("[" + i + "] '" + cc[i] + "'");
                }
                break block21;
            }
            case 'I':
            {
                int[] ii = (int[]) what;
                for (int i = 0; i < ii.length; ++i)
                {
                    System.out.println("[" + i + "] " + ii[i]);
                }
                break block21;
            }
            case 'J':
            {
                long[] jj = (long[]) what;
                for (int i = 0; i < jj.length; ++i)
                {
                    System.out.println("[" + i + "] " + jj[i]);
                }
                break block21;
            }
            case 'F':
            {
                float[] ff = (float[]) what;
                for (int i = 0; i < ff.length; ++i)
                {
                    System.out.println("[" + i + "] " + ff[i]);
                }
                break block21;
            }
            case 'D':
            {
                double[] dd = (double[]) what;
                for (int i = 0; i < dd.length; ++i)
                {
                    System.out.println("[" + i + "] " + dd[i]);
                }
                break block21;
            }
            default:
            {
                System.out.println(what);
                break;
            }
            }
            break block21;
        }
        System.out.println(what);
    }
}

public static final boolean parseBoolean(int what)
{
    return what != 0;
}

public static final boolean parseBoolean(String what)
{
    return Boolean.parseBoolean(what);
}

public static final boolean[] parseBoolean(int[] what)
{
    boolean[] outgoing = new boolean[what.length];
    for (int i = 0; i < what.length; ++i)
    {
        outgoing[i] = what[i] != 0;
    }
    return outgoing;
}

public static final boolean[] parseBoolean(String[] what)
{
    boolean[] outgoing = new boolean[what.length];
    for (int i = 0; i < what.length; ++i)
    {
        outgoing[i] = Boolean.parseBoolean(what[i]);
    }
    return outgoing;
}

public static final byte parseByte(boolean what)
{
    return what ? (byte) 1 : 0;
}

public static final byte parseByte(char what)
{
    return (byte) what;
}

public static final byte parseByte(int what)
{
    return (byte) what;
}

public static final byte parseByte(float what)
{
    return (byte) what;
}

public static final byte[] parseByte(boolean[] what)
{
    byte[] outgoing = new byte[what.length];
    for (int i = 0; i < what.length; ++i)
    {
        outgoing[i] = what[i] ? (byte) 1 : 0;
    }
    return outgoing;
}

public static final byte[] parseByte(char[] what)
{
    byte[] outgoing = new byte[what.length];
    for (int i = 0; i < what.length; ++i)
    {
        outgoing[i] = (byte) what[i];
    }
    return outgoing;
}

public static final byte[] parseByte(int[] what)
{
    byte[] outgoing = new byte[what.length];
    for (int i = 0; i < what.length; ++i)
    {
        outgoing[i] = (byte) what[i];
    }
    return outgoing;
}

public static final byte[] parseByte(float[] what)
{
    byte[] outgoing = new byte[what.length];
    for (int i = 0; i < what.length; ++i)
    {
        outgoing[i] = (byte) what[i];
    }
    return outgoing;
}

public static final char parseChar(byte what)
{
    return (char) (what & 255);
}

public static final char parseChar(int what)
{
    return (char) what;
}

public static final char[] parseChar(byte[] what)
{
    char[] outgoing = new char[what.length];
    for (int i = 0; i < what.length; ++i)
    {
        outgoing[i] = (char) (what[i] & 255);
    }
    return outgoing;
}

public static final char[] parseChar(int[] what)
{
    char[] outgoing = new char[what.length];
    for (int i = 0; i < what.length; ++i)
    {
        outgoing[i] = (char) what[i];
    }
    return outgoing;
}

public static final int parseInt(boolean what)
{
    return what ? 1 : 0;
}

public static final int parseInt(byte what)
{
    return what & 255;
}

public static final int parseInt(char what)
{
    return what;
}

public static final int parseInt(float what)
{
    return (int) what;
}

public static final int parseInt(String what)
{
    return PApplet.parseInt(what, 0);
}

public static final int parseInt(String what, int otherwise)
{
    try
    {
        int offset = what.indexOf(46);
        if (offset == -1)
        {
            return Integer.parseInt(what);
        }
        return Integer.parseInt(what.substring(0, offset));
    }
    catch (NumberFormatException offset)
    {
        return otherwise;
    }
}

public static final int[] parseInt(boolean[] what)
{
    int[] list = new int[what.length];
    for (int i = 0; i < what.length; ++i)
    {
        list[i] = what[i] ? 1 : 0;
    }
    return list;
}

public static final int[] parseInt(byte[] what)
{
    int[] list = new int[what.length];
    for (int i = 0; i < what.length; ++i)
    {
        list[i] = what[i] & 255;
    }
    return list;
}

public static final int[] parseInt(char[] what)
{
    int[] list = new int[what.length];
    for (int i = 0; i < what.length; ++i)
    {
        list[i] = what[i];
    }
    return list;
}

public static int[] parseInt(float[] what)
{
    int[] inties = new int[what.length];
    for (int i = 0; i < what.length; ++i)
    {
        inties[i] = (int) what[i];
    }
    return inties;
}

public static int[] parseInt(String[] what)
{
    return PApplet.parseInt(what, 0);
}

public static int[] parseInt(String[] what, int missing)
{
    int[] output = new int[what.length];
    for (int i = 0; i < what.length; ++i)
    {
        try
        {
            output[i] = Integer.parseInt(what[i]);
            continue;
        }
        catch (NumberFormatException e)
        {
            output[i] = missing;
        }
    }
    return output;
}

public static final float parseFloat(int what)
{
    return what;
}

public static final float parseFloat(String what)
{
    return PApplet.parseFloat(what, Float.NaN);
}

public static final float parseFloat(String what, float otherwise)
{
    try
    {
        return Float.parseFloat(what);
    }
    catch (NumberFormatException numberFormatException)
    {
        return otherwise;
    }
}

public static final float[] parseFloat(byte[] what)
{
    float[] floaties = new float[what.length];
    for (int i = 0; i < what.length; ++i)
    {
        floaties[i] = what[i];
    }
    return floaties;
}

public static final float[] parseFloat(int[] what)
{
    float[] floaties = new float[what.length];
    for (int i = 0; i < what.length; ++i)
    {
        floaties[i] = what[i];
    }
    return floaties;
}

public static final float[] parseFloat(String[] what)
{
    return PApplet.parseFloat(what, Float.NaN);
}

public static final float[] parseFloat(String[] what, float missing)
{
    float[] output = new float[what.length];
    for (int i = 0; i < what.length; ++i)
    {
        try
        {
            output[i] = Float.parseFloat(what[i]);
            continue;
        }
        catch (NumberFormatException e)
        {
            output[i] = missing;
        }
    }
    return output;
}

public static final String str(boolean x)
{
    return String.valueOf(x);
}

public static final String str(byte x)
{
    return String.valueOf(x);
}

public static final String str(char x)
{
    return String.valueOf(x);
}

public static final String str(int x)
{
    return String.valueOf(x);
}

public static final String str(float x)
{
    return String.valueOf(x);
}

public static final String[] str(boolean[] x)
{
    String[] s = new String[x.length];
    for (int i = 0; i < x.length; ++i)
    {
        s[i] = String.valueOf(x[i]);
    }
    return s;
}

public static final String[] str(byte[] x)
{
    String[] s = new String[x.length];
    for (int i = 0; i < x.length; ++i)
    {
        s[i] = String.valueOf(x[i]);
    }
    return s;
}

public static final String[] str(char[] x)
{
    String[] s = new String[x.length];
    for (int i = 0; i < x.length; ++i)
    {
        s[i] = String.valueOf(x[i]);
    }
    return s;
}

public static final String[] str(int[] x)
{
    String[] s = new String[x.length];
    for (int i = 0; i < x.length; ++i)
    {
        s[i] = String.valueOf(x[i]);
    }
    return s;
}

public static final String[] str(float[] x)
{
    String[] s = new String[x.length];
    for (int i = 0; i < x.length; ++i)
    {
        s[i] = String.valueOf(x[i]);
    }
    return s;
}

public static String nf(float num)
{
    int inum = (int) num;
    if (num == (float) inum)
    {
        return PApplet.str(inum);
    }
    return PApplet.str(num);
}

public static String[] nf(float[] nums)
{
    String[] outgoing = new String[nums.length];
    for (int i = 0; i < nums.length; ++i)
    {
        outgoing[i] = PApplet.nf(nums[i]);
    }
    return outgoing;
}

public static String[] nf(int[] nums, int digits)
{
    String[] formatted = new String[nums.length];
    for (int i = 0; i < formatted.length; ++i)
    {
        formatted[i] = PApplet.nf(nums[i], digits);
    }
    return formatted;
}

public static String nf(int num, int digits)
{
    if (int_nf != null && int_nf_digits == digits && !int_nf_commas)
    {
        return int_nf.format(num);
    }
    int_nf = NumberFormat.getInstance();
    int_nf.setGroupingUsed(false);
    int_nf_commas = false;
    int_nf.setMinimumIntegerDigits(digits);
    int_nf_digits = digits;
    return int_nf.format(num);
}

public static String[] nfc(int[] nums)
{
    String[] formatted = new String[nums.length];
    for (int i = 0; i < formatted.length; ++i)
    {
        formatted[i] = PApplet.nfc(nums[i]);
    }
    return formatted;
}

public static String nfc(int num)
{
    if (int_nf != null && int_nf_digits == 0 && int_nf_commas)
    {
        return int_nf.format(num);
    }
    int_nf = NumberFormat.getInstance();
    int_nf.setGroupingUsed(true);
    int_nf_commas = true;
    int_nf.setMinimumIntegerDigits(0);
    int_nf_digits = 0;
    return int_nf.format(num);
}

public static String nfs(int num, int digits)
{
    return num < 0 ? PApplet.nf(num, digits) : ' ' + PApplet.nf(num, digits);
}

public static String[] nfs(int[] nums, int digits)
{
    String[] formatted = new String[nums.length];
    for (int i = 0; i < formatted.length; ++i)
    {
        formatted[i] = PApplet.nfs(nums[i], digits);
    }
    return formatted;
}

public static String nfp(int num, int digits)
{
    return num < 0 ? PApplet.nf(num, digits) : '+' + PApplet.nf(num, digits);
}

public static String[] nfp(int[] nums, int digits)
{
    String[] formatted = new String[nums.length];
    for (int i = 0; i < formatted.length; ++i)
    {
        formatted[i] = PApplet.nfp(nums[i], digits);
    }
    return formatted;
}

public static String[] nf(float[] nums, int left, int right)
{
    String[] formatted = new String[nums.length];
    for (int i = 0; i < formatted.length; ++i)
    {
        formatted[i] = PApplet.nf(nums[i], left, right);
    }
    return formatted;
}

public static String nf(float num, int left, int right)
{
    if (float_nf != null && float_nf_left == left && float_nf_right == right && !float_nf_commas)
    {
        return float_nf.format(num);
    }
    float_nf = NumberFormat.getInstance();
    float_nf.setGroupingUsed(false);
    float_nf_commas = false;
    if (left != 0)
    {
        float_nf.setMinimumIntegerDigits(left);
    }
    if (right != 0)
    {
        float_nf.setMinimumFractionDigits(right);
        float_nf.setMaximumFractionDigits(right);
    }
    float_nf_left = left;
    float_nf_right = right;
    return float_nf.format(num);
}

public static String[] nfc(float[] nums, int right)
{
    String[] formatted = new String[nums.length];
    for (int i = 0; i < formatted.length; ++i)
    {
        formatted[i] = PApplet.nfc(nums[i], right);
    }
    return formatted;
}

public static String nfc(float num, int right)
{
    if (float_nf != null && float_nf_left == 0 && float_nf_right == right && float_nf_commas)
    {
        return float_nf.format(num);
    }
    float_nf = NumberFormat.getInstance();
    float_nf.setGroupingUsed(true);
    float_nf_commas = true;
    if (right != 0)
    {
        float_nf.setMinimumFractionDigits(right);
        float_nf.setMaximumFractionDigits(right);
    }
    float_nf_left = 0;
    float_nf_right = right;
    return float_nf.format(num);
}

public static String[] nfs(float[] nums, int left, int right)
{
    String[] formatted = new String[nums.length];
    for (int i = 0; i < formatted.length; ++i)
    {
        formatted[i] = PApplet.nfs(nums[i], left, right);
    }
    return formatted;
}

public static String nfs(float num, int left, int right)
{
    return num < 0.0f ? PApplet.nf(num, left, right) : ' ' + PApplet.nf(num, left, right);
}

public static String[] nfp(float[] nums, int left, int right)
{
    String[] formatted = new String[nums.length];
    for (int i = 0; i < formatted.length; ++i)
    {
        formatted[i] = PApplet.nfp(nums[i], left, right);
    }
    return formatted;
}

public static String nfp(float num, int left, int right)
{
    return num < 0.0f ? PApplet.nf(num, left, right) : '+' + PApplet.nf(num, left, right);
}

public static final String hex(byte value)
{
    return PApplet.hex(value, 2);
}

public static final String hex(char value)
{
    return PApplet.hex(value, 4);
}

public static final String hex(int value)
{
    return PApplet.hex(value, 8);
}

public static final String hex(int value, int digits)
{
    int length;
    String stuff = Integer.toHexString(value).toUpperCase();
    if (digits > 8)
    {
        digits = 8;
    }
    if ((length = stuff.length()) > digits)
    {
        return stuff.substring(length - digits);
    }
    if (length < digits)
    {
        return "00000000".substring(8 - (digits - length)) + stuff;
    }
    return stuff;
}

public static final int unhex(String value)
{
    return (int) Long.parseLong(value, 16);
}

public static final String binary(byte value)
{
    return PApplet.binary(value, 8);
}

public static final String binary(char value)
{
    return PApplet.binary(value, 16);
}

public static final String binary(int value)
{
    return PApplet.binary(value, 32);
}

public static final String binary(int value, int digits)
{
    int length;
    String stuff = Integer.toBinaryString(value);
    if (digits > 32)
    {
        digits = 32;
    }
    if ((length = stuff.length()) > digits)
    {
        return stuff.substring(length - digits);
    }
    if (length < digits)
    {
        int offset = 32 - (digits - length);
        return "00000000000000000000000000000000".substring(offset) + stuff;
    }
    return stuff;
}

public static final int unbinary(String value)
{
    return Integer.parseInt(value, 2);
}

public static final float abs(float n)
{
    return n < 0.0f ? -n : n;
}

public static final int abs(int n)
{
    return n < 0 ? -n : n;
}

public static final float sq(float n)
{
    return n * n;
}

public static final float sqrt(float n)
{
    return (float) Math.sqrt(n);
}

public static final float log(float n)
{
    return (float) Math.log(n);
}

public static final float exp(float n)
{
    return (float) Math.exp(n);
}

public static final float pow(float n, float e)
{
    return (float) Math.pow(n, e);
}

public static final int max(int a, int b)
{
    return a > b ? a : b;
}

public static final float max(float a, float b)
{
    return a > b ? a : b;
}

public static final int max(int a, int b, int c)
{
    return a > b ? (a > c ? a : c) : (b > c ? b : c);
}

public static final float max(float a, float b, float c)
{
    return a > b ? (a > c ? a : c) : (b > c ? b : c);
}

public static final int max(int[] list)
{
    if (list.length == 0)
    {
        throw new ArrayIndexOutOfBoundsException(ERROR_MIN_MAX);
    }
    int max = list[0];
    for (int i = 1; i < list.length; ++i)
    {
        if (list[i] <= max)
            continue;
        max = list[i];
    }
    return max;
}

public static final float max(float[] list)
{
    if (list.length == 0)
    {
        throw new ArrayIndexOutOfBoundsException(ERROR_MIN_MAX);
    }
    float max = list[0];
    for (int i = 1; i < list.length; ++i)
    {
        if (!(list[i] > max))
            continue;
        max = list[i];
    }
    return max;
}

public static final int min(int a, int b)
{
    return a < b ? a : b;
}

public static final float min(float a, float b)
{
    return a < b ? a : b;
}

public static final int min(int a, int b, int c)
{
    return a < b ? (a < c ? a : c) : (b < c ? b : c);
}

public static final float min(float a, float b, float c)
{
    return a < b ? (a < c ? a : c) : (b < c ? b : c);
}

public static final int min(int[] list)
{
    if (list.length == 0)
    {
        throw new ArrayIndexOutOfBoundsException(ERROR_MIN_MAX);
    }
    int min = list[0];
    for (int i = 1; i < list.length; ++i)
    {
        if (list[i] >= min)
            continue;
        min = list[i];
    }
    return min;
}

public static final float min(float[] list)
{
    if (list.length == 0)
    {
        throw new ArrayIndexOutOfBoundsException(ERROR_MIN_MAX);
    }
    float min = list[0];
    for (int i = 1; i < list.length; ++i)
    {
        if (!(list[i] < min))
            continue;
        min = list[i];
    }
    return min;
}

public static final int constrain(int amt, int low, int high)
{
    return amt < low ? low : (amt > high ? high : amt);
}

public static final float constrain(float amt, float low, float high)
{
    return amt < low ? low : (amt > high ? high : amt);
}

public static final float sin(float angle)
{
    return (float) Math.sin(angle);
}

public static final float cos(float angle)
{
    return (float) Math.cos(angle);
}

public static final float tan(float angle)
{
    return (float) Math.tan(angle);
}

public static final float asin(float value)
{
    return (float) Math.asin(value);
}

public static final float acos(float value)
{
    return (float) Math.acos(value);
}

public static final float atan(float value)
{
    return (float) Math.atan(value);
}

public static final float atan2(float y, float x)
{
    return (float) Math.atan2(y, x);
}

public static final float degrees(float radians)
{
    return radians * 57.295776f;
}

public static final float radians(float degrees)
{
    return degrees * 0.017453292f;
}

public static final int ceil(float n)
{
    return (int) Math.ceil(n);
}

public static final int floor(float n)
{
    return (int) Math.floor(n);
}

public static final int round(float n)
{
    return Math.round(n);
}

public static final float mag(float a, float b)
{
    return (float) Math.sqrt(a * a + b * b);
}

public static final float mag(float a, float b, float c)
{
    return (float) Math.sqrt(a * a + b * b + c * c);
}

public static final float dist(float x1, float y1, float x2, float y2)
{
    return PApplet.sqrt(PApplet.sq(x2 - x1) + PApplet.sq(y2 - y1));
}

public static final float dist(float x1, float y1, float z1, float x2, float y2, float z2)
{
    return PApplet.sqrt(PApplet.sq(x2 - x1) + PApplet.sq(y2 - y1) + PApplet.sq(z2 - z1));
}

public static final float lerp(float start, float stop, float amt)
{
    return start + (stop - start) * amt;
}

public static final float norm(float value, float start, float stop)
{
    return (value - start) / (stop - start);
}

public static final float map(float value, float start1, float stop1, float start2, float stop2)
{
    float outgoing = start2 + (stop2 - start2) * ((value - start1) / (stop1 - start1));
    String badness = null;
    if (outgoing != outgoing)
    {
        badness = "NaN (not a number)";
    }
    else if (outgoing == Float.NEGATIVE_INFINITY || outgoing == Float.POSITIVE_INFINITY)
    {
        badness = "infinity";
    }
    if (badness != null)
    {
        String msg = String.format("map(%s, %s, %s, %s, %s) called, which returns %s", PApplet.nf(value),
                                   PApplet.nf(start1), PApplet.nf(stop1), PApplet.nf(start2), PApplet.nf(stop2), badness);
        throw new ArithmeticException(msg);
    }
    return outgoing;
}

public final float random(float high)
{
    if (high == 0.0f || high != high)
    {
        return 0.0f;
    }
    if (this.internalRandom == null)
    {
        this.internalRandom = new Random();
    }
    float value = 0.0f;
    while ((value = this.internalRandom.nextFloat() * high) == high)
    {
    }
    return value;
}

public final float randomGaussian()
{
    if (this.internalRandom == null)
    {
        this.internalRandom = new Random();
    }
    return (float) this.internalRandom.nextGaussian();
}

public final float random(float low, float high)
{
    if (low >= high)
    {
        return low;
    }
    float diff = high - low;
    float value = 0.0f;
    while ((value = this.random(diff) + low) == high)
    {
    }
    return value;
}

public final void randomSeed(long seed)
{
    if (this.internalRandom == null)
    {
        this.internalRandom = new Random();
    }
    this.internalRandom.setSeed(seed);
}

public float noise(float x)
{
    return this.noise(x, 0.0f, 0.0f);
}

public float noise(float x, float y)
{
    return this.noise(x, y, 0.0f);
}

public float noise(float x, float y, float z)
{
    if (this.perlin == null)
    {
        if (this.perlinRandom == null)
        {
            this.perlinRandom = new Random();
        }
        this.perlin = new float[4096];
        for (int i = 0; i < 4096; ++i)
        {
            this.perlin[i] = this.perlinRandom.nextFloat();
        }
        this.perlin_cosTable = PApplet.cosLUT;
        this.perlin_PI = 720;
        this.perlin_TWOPI = 720;
        this.perlin_PI >>= 1;
    }
    if (x < 0.0f)
    {
        x = -x;
    }
    if (y < 0.0f)
    {
        y = -y;
    }
    if (z < 0.0f)
    {
        z = -z;
    }
    int xi = (int) x;
    int yi = (int) y;
    int zi = (int) z;
    float xf = x - (float) xi;
    float yf = y - (float) yi;
    float zf = z - (float) zi;
    float r = 0.0f;
    float ampl = 0.5f;
    for (int i = 0; i < this.perlin_octaves; ++i)
    {
        int of = xi + (yi << 4) + (zi << 8);
        float rxf = this.noise_fsc(xf);
        float ryf = this.noise_fsc(yf);
        float n1 = this.perlin[of & 4095];
        n1 += rxf * (this.perlin[of + 1 & 4095] - n1);
        float n2 = this.perlin[of + 16 & 4095];
        n2 += rxf * (this.perlin[of + 16 + 1 & 4095] - n2);
        n1 += ryf * (n2 - n1);
        n2 = this.perlin[(of += 256) & 4095];
        n2 += rxf * (this.perlin[of + 1 & 4095] - n2);
        float n3 = this.perlin[of + 16 & 4095];
        n3 += rxf * (this.perlin[of + 16 + 1 & 4095] - n3);
        n2 += ryf * (n3 - n2);
        n1 += this.noise_fsc(zf) * (n2 - n1);
        r += n1 * ampl;
        ampl *= this.perlin_amp_falloff;
        xi <<= 1;
        xf *= 2.0f;
        yi <<= 1;
        yf *= 2.0f;
        zi <<= 1;
        zf *= 2.0f;
        if (xf >= 1.0f)
        {
            ++xi;
            xf -= 1.0f;
        }
        if (yf >= 1.0f)
        {
            ++yi;
            yf -= 1.0f;
        }
        if (!(zf >= 1.0f))
            continue;
        ++zi;
        zf -= 1.0f;
    }
    return r;
}

private float noise_fsc(float i)
{
    return 0.5f * (1.0f - this.perlin_cosTable[(int) (i * (float) this.perlin_PI) % this.perlin_TWOPI]);
}

public void noiseDetail(int lod)
{
    if (lod > 0)
    {
        this.perlin_octaves = lod;
    }
}

public void noiseDetail(int lod, float falloff)
{
    if (lod > 0)
    {
        this.perlin_octaves = lod;
    }
    if (falloff > 0.0f)
    {
        this.perlin_amp_falloff = falloff;
    }
}

public void noiseSeed(long seed)
{
    if (this.perlinRandom == null)
    {
        this.perlinRandom = new Random();
    }
    this.perlinRandom.setSeed(seed);
    this.perlin = null;
}

public static byte[] sort(byte[] list)
{
    return PApplet.sort(list, list.length);
}

public static byte[] sort(byte[] list, int count)
{
    byte[] outgoing = new byte[list.length];
    System.arraycopy(list, 0, outgoing, 0, list.length);
    Arrays.sort(outgoing, 0, count);
    return outgoing;
}

public static char[] sort(char[] list)
{
    return PApplet.sort(list, list.length);
}

public static char[] sort(char[] list, int count)
{
    char[] outgoing = new char[list.length];
    System.arraycopy(list, 0, outgoing, 0, list.length);
    Arrays.sort(outgoing, 0, count);
    return outgoing;
}

public static int[] sort(int[] list)
{
    return PApplet.sort(list, list.length);
}

public static int[] sort(int[] list, int count)
{
    int[] outgoing = new int[list.length];
    System.arraycopy(list, 0, outgoing, 0, list.length);
    Arrays.sort(outgoing, 0, count);
    return outgoing;
}

public static float[] sort(float[] list)
{
    return PApplet.sort(list, list.length);
}

public static float[] sort(float[] list, int count)
{
    float[] outgoing = new float[list.length];
    System.arraycopy(list, 0, outgoing, 0, list.length);
    Arrays.sort(outgoing, 0, count);
    return outgoing;
}

public static String[] sort(String[] list)
{
    return PApplet.sort(list, list.length);
}

public static String[] sort(String[] list, int count)
{
    String[] outgoing = new String[list.length];
    System.arraycopy(list, 0, outgoing, 0, list.length);
    Arrays.sort(outgoing, 0, count);
    return outgoing;
}

public static void arrayCopy(Object src, int srcPosition, Object dst, int dstPosition, int length)
{
    System.arraycopy(src, srcPosition, dst, dstPosition, length);
}

public static void arrayCopy(Object src, Object dst, int length)
{
    System.arraycopy(src, 0, dst, 0, length);
}

public static void arrayCopy(Object src, Object dst)
{
    System.arraycopy(src, 0, dst, 0, Array.getLength(src));
}

@Deprecated
public static void arraycopy(Object src, int srcPosition, Object dst, int dstPosition, int length)
{
    System.arraycopy(src, srcPosition, dst, dstPosition, length);
}

@Deprecated
public static void arraycopy(Object src, Object dst, int length)
{
    System.arraycopy(src, 0, dst, 0, length);
}

@Deprecated
public static void arraycopy(Object src, Object dst)
{
    System.arraycopy(src, 0, dst, 0, Array.getLength(src));
}

public static boolean[] expand(boolean[] list)
{
    return PApplet.expand(list, list.length > 0 ? list.length << 1 : 1);
}

public static boolean[] expand(boolean[] list, int newSize)
{
    boolean[] temp = new boolean[newSize];
    System.arraycopy(list, 0, temp, 0, Math.min(newSize, list.length));
    return temp;
}

public static byte[] expand(byte[] list)
{
    return PApplet.expand(list, list.length > 0 ? list.length << 1 : 1);
}

public static byte[] expand(byte[] list, int newSize)
{
    byte[] temp = new byte[newSize];
    System.arraycopy(list, 0, temp, 0, Math.min(newSize, list.length));
    return temp;
}

public static char[] expand(char[] list)
{
    return PApplet.expand(list, list.length > 0 ? list.length << 1 : 1);
}

public static char[] expand(char[] list, int newSize)
{
    char[] temp = new char[newSize];
    System.arraycopy(list, 0, temp, 0, Math.min(newSize, list.length));
    return temp;
}

public static int[] expand(int[] list)
{
    return PApplet.expand(list, list.length > 0 ? list.length << 1 : 1);
}

public static int[] expand(int[] list, int newSize)
{
    int[] temp = new int[newSize];
    System.arraycopy(list, 0, temp, 0, Math.min(newSize, list.length));
    return temp;
}

public static long[] expand(long[] list)
{
    return PApplet.expand(list, list.length > 0 ? list.length << 1 : 1);
}

public static long[] expand(long[] list, int newSize)
{
    long[] temp = new long[newSize];
    System.arraycopy(list, 0, temp, 0, Math.min(newSize, list.length));
    return temp;
}

public static float[] expand(float[] list)
{
    return PApplet.expand(list, list.length > 0 ? list.length << 1 : 1);
}

public static float[] expand(float[] list, int newSize)
{
    float[] temp = new float[newSize];
    System.arraycopy(list, 0, temp, 0, Math.min(newSize, list.length));
    return temp;
}

public static double[] expand(double[] list)
{
    return PApplet.expand(list, list.length > 0 ? list.length << 1 : 1);
}

public static double[] expand(double[] list, int newSize)
{
    double[] temp = new double[newSize];
    System.arraycopy(list, 0, temp, 0, Math.min(newSize, list.length));
    return temp;
}

public static String[] expand(String[] list)
{
    return PApplet.expand(list, list.length > 0 ? list.length << 1 : 1);
}

public static String[] expand(String[] list, int newSize)
{
    String[] temp = new String[newSize];
    System.arraycopy(list, 0, temp, 0, Math.min(newSize, list.length));
    return temp;
}

public static Object expand(Object array)
{
    int len = Array.getLength(array);
    return PApplet.expand(array, len > 0 ? len << 1 : 1);
}

public static Object expand(Object list, int newSize)
{
    Class<?> type = list.getClass().getComponentType();
    Object temp = Array.newInstance(type, newSize);
    System.arraycopy(list, 0, temp, 0, Math.min(Array.getLength(list), newSize));
    return temp;
}

public static byte[] append(byte[] array, byte value)
{
    array = PApplet.expand(array, array.length + 1);
    array[array.length - 1] = value;
    return array;
}

public static char[] append(char[] array, char value)
{
    array = PApplet.expand(array, array.length + 1);
    array[array.length - 1] = value;
    return array;
}

public static int[] append(int[] array, int value)
{
    array = PApplet.expand(array, array.length + 1);
    array[array.length - 1] = value;
    return array;
}

public static float[] append(float[] array, float value)
{
    array = PApplet.expand(array, array.length + 1);
    array[array.length - 1] = value;
    return array;
}

public static String[] append(String[] array, String value)
{
    array = PApplet.expand(array, array.length + 1);
    array[array.length - 1] = value;
    return array;
}

public static Object append(Object array, Object value)
{
    int length = Array.getLength(array);
    array = PApplet.expand(array, length + 1);
    Array.set(array, length, value);
    return array;
}

public static boolean[] shorten(boolean[] list)
{
    return PApplet.subset(list, 0, list.length - 1);
}

public static byte[] shorten(byte[] list)
{
    return PApplet.subset(list, 0, list.length - 1);
}

public static char[] shorten(char[] list)
{
    return PApplet.subset(list, 0, list.length - 1);
}

public static int[] shorten(int[] list)
{
    return PApplet.subset(list, 0, list.length - 1);
}

public static float[] shorten(float[] list)
{
    return PApplet.subset(list, 0, list.length - 1);
}

public static String[] shorten(String[] list)
{
    return PApplet.subset(list, 0, list.length - 1);
}

public static Object shorten(Object list)
{
    int length = Array.getLength(list);
    return PApplet.subset(list, 0, length - 1);
}

public static final boolean[] splice(boolean[] list, boolean value, int index)
{
    boolean[] outgoing = new boolean[list.length + 1];
    System.arraycopy(list, 0, outgoing, 0, index);
    outgoing[index] = value;
    System.arraycopy(list, index, outgoing, index + 1, list.length - index);
    return outgoing;
}

public static final boolean[] splice(boolean[] list, boolean[] value, int index)
{
    boolean[] outgoing = new boolean[list.length + value.length];
    System.arraycopy(list, 0, outgoing, 0, index);
    System.arraycopy(value, 0, outgoing, index, value.length);
    System.arraycopy(list, index, outgoing, index + value.length, list.length - index);
    return outgoing;
}

public static final byte[] splice(byte[] list, byte value, int index)
{
    byte[] outgoing = new byte[list.length + 1];
    System.arraycopy(list, 0, outgoing, 0, index);
    outgoing[index] = value;
    System.arraycopy(list, index, outgoing, index + 1, list.length - index);
    return outgoing;
}

public static final byte[] splice(byte[] list, byte[] value, int index)
{
    byte[] outgoing = new byte[list.length + value.length];
    System.arraycopy(list, 0, outgoing, 0, index);
    System.arraycopy(value, 0, outgoing, index, value.length);
    System.arraycopy(list, index, outgoing, index + value.length, list.length - index);
    return outgoing;
}

public static final char[] splice(char[] list, char value, int index)
{
    char[] outgoing = new char[list.length + 1];
    System.arraycopy(list, 0, outgoing, 0, index);
    outgoing[index] = value;
    System.arraycopy(list, index, outgoing, index + 1, list.length - index);
    return outgoing;
}

public static final char[] splice(char[] list, char[] value, int index)
{
    char[] outgoing = new char[list.length + value.length];
    System.arraycopy(list, 0, outgoing, 0, index);
    System.arraycopy(value, 0, outgoing, index, value.length);
    System.arraycopy(list, index, outgoing, index + value.length, list.length - index);
    return outgoing;
}

public static final int[] splice(int[] list, int value, int index)
{
    int[] outgoing = new int[list.length + 1];
    System.arraycopy(list, 0, outgoing, 0, index);
    outgoing[index] = value;
    System.arraycopy(list, index, outgoing, index + 1, list.length - index);
    return outgoing;
}

public static final int[] splice(int[] list, int[] value, int index)
{
    int[] outgoing = new int[list.length + value.length];
    System.arraycopy(list, 0, outgoing, 0, index);
    System.arraycopy(value, 0, outgoing, index, value.length);
    System.arraycopy(list, index, outgoing, index + value.length, list.length - index);
    return outgoing;
}

public static final float[] splice(float[] list, float value, int index)
{
    float[] outgoing = new float[list.length + 1];
    System.arraycopy(list, 0, outgoing, 0, index);
    outgoing[index] = value;
    System.arraycopy(list, index, outgoing, index + 1, list.length - index);
    return outgoing;
}

public static final float[] splice(float[] list, float[] value, int index)
{
    float[] outgoing = new float[list.length + value.length];
    System.arraycopy(list, 0, outgoing, 0, index);
    System.arraycopy(value, 0, outgoing, index, value.length);
    System.arraycopy(list, index, outgoing, index + value.length, list.length - index);
    return outgoing;
}

public static final String[] splice(String[] list, String value, int index)
{
    String[] outgoing = new String[list.length + 1];
    System.arraycopy(list, 0, outgoing, 0, index);
    outgoing[index] = value;
    System.arraycopy(list, index, outgoing, index + 1, list.length - index);
    return outgoing;
}

public static final String[] splice(String[] list, String[] value, int index)
{
    String[] outgoing = new String[list.length + value.length];
    System.arraycopy(list, 0, outgoing, 0, index);
    System.arraycopy(value, 0, outgoing, index, value.length);
    System.arraycopy(list, index, outgoing, index + value.length, list.length - index);
    return outgoing;
}

public static final Object splice(Object list, Object value, int index)
{
    Class<?> type = list.getClass().getComponentType();
    Object outgoing = null;
    int length = Array.getLength(list);
    if (value.getClass().getName().charAt(0) == '[')
    {
        int vlength = Array.getLength(value);
        outgoing = Array.newInstance(type, length + vlength);
        System.arraycopy(list, 0, outgoing, 0, index);
        System.arraycopy(value, 0, outgoing, index, vlength);
        System.arraycopy(list, index, outgoing, index + vlength, length - index);
    }
    else
    {
        outgoing = Array.newInstance(type, length + 1);
        System.arraycopy(list, 0, outgoing, 0, index);
        Array.set(outgoing, index, value);
        System.arraycopy(list, index, outgoing, index + 1, length - index);
    }
    return outgoing;
}

public static boolean[] subset(boolean[] list, int start)
{
    return PApplet.subset(list, start, list.length - start);
}

public static boolean[] subset(boolean[] list, int start, int count)
{
    boolean[] output = new boolean[count];
    System.arraycopy(list, start, output, 0, count);
    return output;
}

public static byte[] subset(byte[] list, int start)
{
    return PApplet.subset(list, start, list.length - start);
}

public static byte[] subset(byte[] list, int start, int count)
{
    byte[] output = new byte[count];
    System.arraycopy(list, start, output, 0, count);
    return output;
}

public static char[] subset(char[] list, int start)
{
    return PApplet.subset(list, start, list.length - start);
}

public static char[] subset(char[] list, int start, int count)
{
    char[] output = new char[count];
    System.arraycopy(list, start, output, 0, count);
    return output;
}

public static int[] subset(int[] list, int start)
{
    return PApplet.subset(list, start, list.length - start);
}

public static int[] subset(int[] list, int start, int count)
{
    int[] output = new int[count];
    System.arraycopy(list, start, output, 0, count);
    return output;
}

public static long[] subset(long[] list, int start)
{
    return PApplet.subset(list, start, list.length - start);
}

public static long[] subset(long[] list, int start, int count)
{
    long[] output = new long[count];
    System.arraycopy(list, start, output, 0, count);
    return output;
}

public static float[] subset(float[] list, int start)
{
    return PApplet.subset(list, start, list.length - start);
}

public static float[] subset(float[] list, int start, int count)
{
    float[] output = new float[count];
    System.arraycopy(list, start, output, 0, count);
    return output;
}

public static double[] subset(double[] list, int start)
{
    return PApplet.subset(list, start, list.length - start);
}

public static double[] subset(double[] list, int start, int count)
{
    double[] output = new double[count];
    System.arraycopy(list, start, output, 0, count);
    return output;
}

public static String[] subset(String[] list, int start)
{
    return PApplet.subset(list, start, list.length - start);
}

public static String[] subset(String[] list, int start, int count)
{
    String[] output = new String[count];
    System.arraycopy(list, start, output, 0, count);
    return output;
}

public static Object subset(Object list, int start)
{
    int length = Array.getLength(list);
    return PApplet.subset(list, start, length - start);
}

public static Object subset(Object list, int start, int count)
{
    Class<?> type = list.getClass().getComponentType();
    Object outgoing = Array.newInstance(type, count);
    System.arraycopy(list, start, outgoing, 0, count);
    return outgoing;
}

public static boolean[] concat(boolean[] a, boolean[] b)
{
    boolean[] c = new boolean[a.length + b.length];
    System.arraycopy(a, 0, c, 0, a.length);
    System.arraycopy(b, 0, c, a.length, b.length);
    return c;
}

public static byte[] concat(byte[] a, byte[] b)
{
    byte[] c = new byte[a.length + b.length];
    System.arraycopy(a, 0, c, 0, a.length);
    System.arraycopy(b, 0, c, a.length, b.length);
    return c;
}

public static char[] concat(char[] a, char[] b)
{
    char[] c = new char[a.length + b.length];
    System.arraycopy(a, 0, c, 0, a.length);
    System.arraycopy(b, 0, c, a.length, b.length);
    return c;
}

public static int[] concat(int[] a, int[] b)
{
    int[] c = new int[a.length + b.length];
    System.arraycopy(a, 0, c, 0, a.length);
    System.arraycopy(b, 0, c, a.length, b.length);
    return c;
}

public static float[] concat(float[] a, float[] b)
{
    float[] c = new float[a.length + b.length];
    System.arraycopy(a, 0, c, 0, a.length);
    System.arraycopy(b, 0, c, a.length, b.length);
    return c;
}

public static String[] concat(String[] a, String[] b)
{
    String[] c = new String[a.length + b.length];
    System.arraycopy(a, 0, c, 0, a.length);
    System.arraycopy(b, 0, c, a.length, b.length);
    return c;
}

public static Object concat(Object a, Object b)
{
    Class<?> type = a.getClass().getComponentType();
    int alength = Array.getLength(a);
    int blength = Array.getLength(b);
    Object outgoing = Array.newInstance(type, alength + blength);
    System.arraycopy(a, 0, outgoing, 0, alength);
    System.arraycopy(b, 0, outgoing, alength, blength);
    return outgoing;
}

public static boolean[] reverse(boolean[] list)
{
    boolean[] outgoing = new boolean[list.length];
    int length1 = list.length - 1;
    for (int i = 0; i < list.length; ++i)
    {
        outgoing[i] = list[length1 - i];
    }
    return outgoing;
}

public static byte[] reverse(byte[] list)
{
    byte[] outgoing = new byte[list.length];
    int length1 = list.length - 1;
    for (int i = 0; i < list.length; ++i)
    {
        outgoing[i] = list[length1 - i];
    }
    return outgoing;
}

public static char[] reverse(char[] list)
{
    char[] outgoing = new char[list.length];
    int length1 = list.length - 1;
    for (int i = 0; i < list.length; ++i)
    {
        outgoing[i] = list[length1 - i];
    }
    return outgoing;
}

public static int[] reverse(int[] list)
{
    int[] outgoing = new int[list.length];
    int length1 = list.length - 1;
    for (int i = 0; i < list.length; ++i)
    {
        outgoing[i] = list[length1 - i];
    }
    return outgoing;
}

public static float[] reverse(float[] list)
{
    float[] outgoing = new float[list.length];
    int length1 = list.length - 1;
    for (int i = 0; i < list.length; ++i)
    {
        outgoing[i] = list[length1 - i];
    }
    return outgoing;
}

public static String[] reverse(String[] list)
{
    String[] outgoing = new String[list.length];
    int length1 = list.length - 1;
    for (int i = 0; i < list.length; ++i)
    {
        outgoing[i] = list[length1 - i];
    }
    return outgoing;
}

public static Object reverse(Object list)
{
    Class<?> type = list.getClass().getComponentType();
    int length = Array.getLength(list);
    Object outgoing = Array.newInstance(type, length);
    for (int i = 0; i < length; ++i)
    {
        Array.set(outgoing, i, Array.get(list, length - 1 - i));
    }
    return outgoing;
}

public static String trim(String str)
{
    if (str == null)
    {
        return null;
    }
    return str.replace('\u00a0', ' ').trim();
}

public static String[] trim(String[] array)
{
    if (array == null)
    {
        return null;
    }
    String[] outgoing = new String[array.length];
    for (int i = 0; i < array.length; ++i)
    {
        if (array[i] == null)
            continue;
        outgoing[i] = PApplet.trim(array[i]);
    }
    return outgoing;
}

public static String join(String[] list, char separator)
{
    return PApplet.join(list, String.valueOf(separator));
}

public static String join(String[] list, String separator)
{
    StringBuilder sb = new StringBuilder();
    for (int i = 0; i < list.length; ++i)
    {
        if (i != 0)
        {
            sb.append(separator);
        }
        sb.append(list[i]);
    }
    return sb.toString();
}

public static String[] splitTokens(String value)
{
    return PApplet.splitTokens(value, " \t\n\r\f\u00a0");
}

public static String[] splitTokens(String value, String delim)
{
    StringTokenizer toker = new StringTokenizer(value, delim);
    String[] pieces = new String[toker.countTokens()];
    int index = 0;
    while (toker.hasMoreTokens())
    {
        pieces[index++] = toker.nextToken();
    }
    return pieces;
}

public static String[] split(String value, char delim)
{
    if (value == null)
    {
        return null;
    }
    char[] chars = value.toCharArray();
    int splitCount = 0;
    for (int i = 0; i < chars.length; ++i)
    {
        if (chars[i] != delim)
            continue;
        ++splitCount;
    }
    if (splitCount == 0)
    {
        String[] splits = new String[] { value };
        return splits;
    }
    String[] splits = new String[splitCount + 1];
    int splitIndex = 0;
    int startIndex = 0;
    for (int i = 0; i < chars.length; ++i)
    {
        if (chars[i] != delim)
            continue;
        splits[splitIndex++] = new String(chars, startIndex, i - startIndex);
        startIndex = i + 1;
    }
    splits[splitIndex] = new String(chars, startIndex, chars.length - startIndex);
    return splits;
}

public static String[] split(String value, String delim)
{
    int index;
    ArrayList<String> items = new ArrayList<String>();
    int offset = 0;
    while ((index = value.indexOf(delim, offset)) != -1)
    {
        items.add(value.substring(offset, index));
        offset = index + delim.length();
    }
    items.add(value.substring(offset));
    String[] outgoing = new String[items.size()];
    items.toArray(outgoing);
    return outgoing;
}

static Pattern matchPattern(String regexp)
{
    Pattern p = null;
    if (matchPatterns == null)
    {
        matchPatterns = new LinkedHashMap<String, Pattern>(16, 0.75f, true)
        {

            @Override
            protected boolean removeEldestEntry(Map.Entry<String, Pattern> eldest)
            {
                return this.size() == 10;
            }
        };
    }
    else
    {
        p = matchPatterns.get(regexp);
    }
    if (p == null)
    {
        p = Pattern.compile(regexp, 40);
        matchPatterns.put(regexp, p);
    }
    return p;
}

public static String[] match(String str, String regexp)
{
    Pattern p = PApplet.matchPattern(regexp);
    Matcher m = p.matcher(str);
    if (m.find())
    {
        int count = m.groupCount() + 1;
        String[] groups = new String[count];
        for (int i = 0; i < count; ++i)
        {
            groups[i] = m.group(i);
        }
        return groups;
    }
    return null;
}

public static String[][] matchAll(String str, String regexp)
{
    int i;
    Pattern p = PApplet.matchPattern(regexp);
    Matcher m = p.matcher(str);
    ArrayList<String[]> results = new ArrayList<String[]>();
    int count = m.groupCount() + 1;
    while (m.find())
    {
        String[] groups = new String[count];
        for (i = 0; i < count; ++i)
        {
            groups[i] = m.group(i);
        }
        results.add(groups);
    }
    if (results.isEmpty())
    {
        return null;
    }
    String[][] matches = new String[results.size()][count];
    for (i = 0; i < matches.length; ++i)
    {
        matches[i] = (String[]) results.get(i);
    }
    return matches;
}
}

class DoubleList implements Iterable<Double>
{
    int count;
    double[] data;

    public DoubleList()
    {
        this.data = new double[10];
    }

    public DoubleList(int length)
    {
        this.data = new double[length];
    }

    public DoubleList(double[] list)
    {
        this.count = list.length;
        this.data = new double[this.count];
        System.arraycopy(list, 0, this.data, 0, this.count);
    }

    public DoubleList(Iterable<Object> iter)
    {
        this(10);
        for (Object o : iter)
        {
            if (o == null)
            {
                this.append(Double.NaN);
                continue;
            }
            if (o instanceof Number)
            {
                this.append(((Number) o).doubleValue());
                continue;
            }
            this.append(PApplet.parseFloat(o.toString().trim()));
        }
        this.crop();
    }

    public /* varargs */ DoubleList(Object... items)
    {
        double missingValue = Double.NaN;
        this.count = items.length;
        this.data = new double[this.count];
        int index = 0;
        for (Object o : items)
        {
            double value = Double.NaN;
            if (o != null)
            {
                if (o instanceof Number)
                {
                    value = ((Number) o).doubleValue();
                }
                else
                {
                    try
                    {
                        value = Double.parseDouble(o.toString().trim());
                    }
                    catch (NumberFormatException nfe)
                    {
                        value = Double.NaN;
                    }
                }
            }
            this.data[index++] = value;
        }
    }

    private void crop()
    {
        if (this.count != this.data.length)
        {
            this.data = PApplet.subset(this.data, 0, this.count);
        }
    }

    public int size()
    {
        return this.count;
    }

    public void resize(int length)
    {
        if (length > this.data.length)
        {
            double[] temp = new double[length];
            System.arraycopy(this.data, 0, temp, 0, this.count);
            this.data = temp;
        }
        else if (length > this.count)
        {
            Arrays.fill(this.data, this.count, length, 0.0);
        }
        this.count = length;
    }

    public void clear()
    {
        this.count = 0;
    }

    public double get(int index)
    {
        if (index >= this.count)
        {
            throw new ArrayIndexOutOfBoundsException(index);
        }
        return this.data[index];
    }

    public void set(int index, double what)
    {
        if (index >= this.count)
        {
            this.data = PApplet.expand(this.data, index + 1);
            for (int i = this.count; i < index; ++i)
            {
                this.data[i] = 0.0;
            }
            this.count = index + 1;
        }
        this.data[index] = what;
    }

    public void push(double value)
    {
        this.append(value);
    }

    public double pop()
    {
        if (this.count == 0)
        {
            throw new RuntimeException("Can't call pop() on an empty list");
        }
        double value = this.get(this.count - 1);
        --this.count;
        return value;
    }

    public double remove(int index)
    {
        if (index < 0 || index >= this.count)
        {
            throw new ArrayIndexOutOfBoundsException(index);
        }
        double entry = this.data[index];
        for (int i = index; i < this.count - 1; ++i)
        {
            this.data[i] = this.data[i + 1];
        }
        --this.count;
        return entry;
    }

    public int removeValue(int value)
    {
        int index = this.index(value);
        if (index != -1)
        {
            this.remove(index);
            return index;
        }
        return -1;
    }

    public int removeValues(int value)
    {
        int i;
        int ii = 0;
        if (Double.isNaN(value))
        {
            for (i = 0; i < this.count; ++i)
            {
                if (Double.isNaN(this.data[i]))
                    continue;
                this.data[ii++] = this.data[i];
            }
        }
        else
        {
            for (i = 0; i < this.count; ++i)
            {
                if (this.data[i] == (double) value)
                    continue;
                this.data[ii++] = this.data[i];
            }
        }
        int removed = this.count - ii;
        this.count = ii;
        return removed;
    }

    public boolean replaceValue(double value, double newValue)
    {
        if (Double.isNaN(value))
        {
            for (int i = 0; i < this.count; ++i)
            {
                if (!Double.isNaN(this.data[i]))
                    continue;
                this.data[i] = newValue;
                return true;
            }
        }
        else
        {
            int index = this.index(value);
            if (index != -1)
            {
                this.data[index] = newValue;
                return true;
            }
        }
        return false;
    }

    public boolean replaceValues(double value, double newValue)
    {
        boolean changed;
        changed = false;
        if (Double.isNaN(value))
        {
            for (int i = 0; i < this.count; ++i)
            {
                if (!Double.isNaN(this.data[i]))
                    continue;
                this.data[i] = newValue;
                changed = true;
            }
        }
        else
        {
            for (int i = 0; i < this.count; ++i)
            {
                if (this.data[i] != value)
                    continue;
                this.data[i] = newValue;
                changed = true;
            }
        }
        return changed;
    }

    public void append(double value)
    {
        if (this.count == this.data.length)
        {
            this.data = PApplet.expand(this.data);
        }
        this.data[this.count++] = value;
    }

    public void append(double[] values)
    {
        for (double v : values)
        {
            this.append(v);
        }
    }

    public void append(DoubleList list)
    {
        for (double v : list.values())
        {
            this.append(v);
        }
    }

    public void appendUnique(double value)
    {
        if (!this.hasValue(value))
        {
            this.append(value);
        }
    }

    public void insert(int index, double value)
    {
        this.insert(index, new double[] { value });
    }

    public void insert(int index, double[] values)
    {
        if (index < 0)
        {
            throw new IllegalArgumentException("insert() index cannot be negative: it was " + index);
        }
        if (index >= this.data.length)
        {
            throw new IllegalArgumentException("insert() index " + index + " is past the end of this list");
        }
        double[] temp = new double[this.count + values.length];
        System.arraycopy(this.data, 0, temp, 0, Math.min(this.count, index));
        System.arraycopy(values, 0, temp, index, values.length);
        System.arraycopy(this.data, index, temp, index + values.length, this.count - index);
        this.count += values.length;
        this.data = temp;
    }

    public void insert(int index, DoubleList list)
    {
        this.insert(index, list.values());
    }

    public int index(double what)
    {
        for (int i = 0; i < this.count; ++i)
        {
            if (this.data[i] != what)
                continue;
            return i;
        }
        return -1;
    }

    public boolean hasValue(double value)
    {
        if (Double.isNaN(value))
        {
            for (int i = 0; i < this.count; ++i)
            {
                if (!Double.isNaN(this.data[i]))
                    continue;
                return true;
            }
        }
        else
        {
            for (int i = 0; i < this.count; ++i)
            {
                if (this.data[i] != value)
                    continue;
                return true;
            }
        }
        return false;
    }

    private void boundsProblem(int index, String method)
    {
        String msg = String.format("The list size is %d. You cannot %s() to element %d.", this.count, method, index);
        throw new ArrayIndexOutOfBoundsException(msg);
    }

    public void add(int index, double amount)
    {
        if (index < this.count)
        {
            double[] arrd = this.data;
            int n = index;
            arrd[n] = arrd[n] + amount;
        }
        else
        {
            this.boundsProblem(index, "add");
        }
    }

    public void sub(int index, double amount)
    {
        if (index < this.count)
        {
            double[] arrd = this.data;
            int n = index;
            arrd[n] = arrd[n] - amount;
        }
        else
        {
            this.boundsProblem(index, "sub");
        }
    }

    public void mult(int index, double amount)
    {
        if (index < this.count)
        {
            double[] arrd = this.data;
            int n = index;
            arrd[n] = arrd[n] * amount;
        }
        else
        {
            this.boundsProblem(index, "mult");
        }
    }

    public void div(int index, double amount)
    {
        if (index < this.count)
        {
            double[] arrd = this.data;
            int n = index;
            arrd[n] = arrd[n] / amount;
        }
        else
        {
            this.boundsProblem(index, "div");
        }
    }

    private void checkMinMax(String functionName)
    {
        if (this.count == 0)
        {
            String msg = String.format("Cannot use %s() on an empty %s.", functionName,
                                       this.getClass().getSimpleName());
            throw new RuntimeException(msg);
        }
    }

    public double min()
    {
        this.checkMinMax("min");
        int index = this.minIndex();
        return index == -1 ? Double.NaN : this.data[index];
    }

    public int minIndex()
    {
        this.checkMinMax("minIndex");
        double m = Double.NaN;
        int mi = -1;
        for (int i = 0; i < this.count; ++i)
        {
            if (this.data[i] != this.data[i])
                continue;
            m = this.data[i];
            mi = i;
            for (int j = i + 1; j < this.count; ++j)
            {
                double d = this.data[j];
                if (Double.isNaN(d) || !(d < m))
                    continue;
                m = this.data[j];
                mi = j;
            }
            break;
        }
        return mi;
    }

    public double max()
    {
        this.checkMinMax("max");
        int index = this.maxIndex();
        return index == -1 ? Double.NaN : this.data[index];
    }

    public int maxIndex()
    {
        this.checkMinMax("maxIndex");
        double m = Double.NaN;
        int mi = -1;
        for (int i = 0; i < this.count; ++i)
        {
            if (this.data[i] != this.data[i])
                continue;
            m = this.data[i];
            mi = i;
            for (int j = i + 1; j < this.count; ++j)
            {
                double d = this.data[j];
                if (Double.isNaN(d) || !(d > m))
                    continue;
                m = this.data[j];
                mi = j;
            }
            break;
        }
        return mi;
    }

    public double sum()
    {
        double sum = 0.0;
        for (int i = 0; i < this.count; ++i)
        {
            sum += this.data[i];
        }
        return sum;
    }

    public void sort()
    {
        Arrays.sort(this.data, 0, this.count);
    }

    public void sortReverse()
    {
        new Sort()
        {

            @Override
            public int size()
            {
                if (DoubleList.this.count == 0)
                {
                    return 0;
                }
                int right = DoubleList.this.count - 1;
                while (DoubleList.this.data[right] != DoubleList.this.data[right])
                {
                    if (--right != -1)
                        continue;
                    return 0;
                }
                for (int i = right; i >= 0; --i)
                {
                    double v = DoubleList.this.data[i];
                    if (v == v)
                        continue;
                    DoubleList.this.data[i] = DoubleList.this.data[right];
                    DoubleList.this.data[right] = v;
                    --right;
                }
                return right + 1;
            }

            @Override
            public int compare(int a, int b)
            {
                double diff = DoubleList.this.data[b] - DoubleList.this.data[a];
                return diff == 0.0 ? 0 : (diff < 0.0 ? -1 : 1);
            }

            @Override
            public void swap(int a, int b)
            {
                double temp = DoubleList.this.data[a];
                DoubleList.this.data[a] = DoubleList.this.data[b];
                DoubleList.this.data[b] = temp;
            }
        } .run();
    }

    public void reverse()
    {
        int ii = this.count - 1;
        for (int i = 0; i < this.count / 2; ++i)
        {
            double t = this.data[i];
            this.data[i] = this.data[ii];
            this.data[ii] = t;
            --ii;
        }
    }

    public void shuffle()
    {
        Random r = new Random();
        int num = this.count;
        while (num > 1)
        {
            int value = r.nextInt(num);
            double temp = this.data[--num];
            this.data[num] = this.data[value];
            this.data[value] = temp;
        }
    }

    public void shuffle(PApplet sketch)
    {
        int num = this.count;
        while (num > 1)
        {
            int value = (int) sketch.random(num);
            double temp = this.data[--num];
            this.data[num] = this.data[value];
            this.data[value] = temp;
        }
    }

    public DoubleList copy()
    {
        DoubleList outgoing = new DoubleList(this.data);
        outgoing.count = this.count;
        return outgoing;
    }

    public double[] values()
    {
        this.crop();
        return this.data;
    }

    @Override
    public Iterator<Double> iterator()
    {
        return new Iterator<Double>()
        {
            int index = -1;

            @Override
            public void remove()
            {
                DoubleList.this.remove(this.index);
                --this.index;
            }

            @Override
            public Double next()
            {
                return DoubleList.this.data[++this.index];
            }

            @Override
            public boolean hasNext()
            {
                return this.index + 1 < DoubleList.this.count;
            }
        };
    }

    public double[] array()
    {
        return this.array(null);
    }

    public double[] array(double[] array)
    {
        if (array == null || array.length != this.count)
        {
            array = new double[this.count];
        }
        System.arraycopy(this.data, 0, array, 0, this.count);
        return array;
    }

    public DoubleList getPercent()
    {
        double sum = 0.0;
        for (double value : this.array())
        {
            sum += value;
        }
        DoubleList outgoing = new DoubleList(this.count);
        for (int i = 0; i < this.count; ++i)
        {
            double percent = this.data[i] / sum;
            outgoing.set(i, percent);
        }
        return outgoing;
    }

    public DoubleList getSubset(int start)
    {
        return this.getSubset(start, this.count - start);
    }

    public DoubleList getSubset(int start, int num)
    {
        double[] subset = new double[num];
        System.arraycopy(this.data, start, subset, 0, num);
        return new DoubleList(subset);
    }

    public String join(String separator)
    {
        if (this.count == 0)
        {
            return "";
        }
        StringBuilder sb = new StringBuilder();
        sb.append(this.data[0]);
        for (int i = 1; i < this.count; ++i)
        {
            sb.append(separator);
            sb.append(this.data[i]);
        }
        return sb.toString();
    }

    public void print()
    {
        for (int i = 0; i < this.count; ++i)
        {
            System.out.format("[%d] %f%n", i, this.data[i]);
        }
    }

    public void write(PrintWriter writer)
    {
        for (int i = 0; i < this.count; ++i)
        {
            writer.println(this.data[i]);
        }
        writer.flush();
    }

    public String toJSON()
    {
        return "[ " + this.join(", ") + " ]";
    }

    public String toString()
    {
        return this.getClass().getSimpleName() + " size=" + this.size() + " " + this.toJSON();
    }

}

class DoubleDict
{
    protected int count;
    protected String[] keys;
    protected double[] values;
    private HashMap<String, Integer> indices = new HashMap();

    public DoubleDict()
    {
        this.count = 0;
        this.keys = new String[10];
        this.values = new double[10];
    }

    public DoubleDict(int length)
    {
        this.count = 0;
        this.keys = new String[length];
        this.values = new double[length];
    }

    public DoubleDict(String[] keys, double[] values)
    {
        if (keys.length != values.length)
        {
            throw new IllegalArgumentException("key and value arrays must be the same length");
        }
        this.keys = keys;
        this.values = values;
        this.count = keys.length;
        for (int i = 0; i < this.count; ++i)
        {
            this.indices.put(keys[i], i);
        }
    }

    public DoubleDict(Object[][] pairs)
    {
        this.count = pairs.length;
        this.keys = new String[this.count];
        this.values = new double[this.count];
        for (int i = 0; i < this.count; ++i)
        {
            this.keys[i] = (String) pairs[i][0];
            this.values[i] = ((Float) pairs[i][1]).floatValue();
            this.indices.put(this.keys[i], i);
        }
    }

    public DoubleDict(Map<String, Double> incoming)
    {
        this.count = incoming.size();
        this.keys = new String[this.count];
        this.values = new double[this.count];
        int index = 0;
        for (Map.Entry<String, Double> e : incoming.entrySet())
        {
            this.keys[index] = e.getKey();
            this.values[index] = e.getValue();
            this.indices.put(this.keys[index], index);
            ++index;
        }
    }

    public int size()
    {
        return this.count;
    }

    public void resize(int length)
    {
        if (length == this.count)
        {
            return;
        }
        if (length > this.count)
        {
            throw new IllegalArgumentException("resize() can only be used to shrink the dictionary");
        }
        if (length < 1)
        {
            throw new IllegalArgumentException("resize(" + length + ") is too small, use 1 or higher");
        }
        String[] newKeys = new String[length];
        double[] newValues = new double[length];
        PApplet.arrayCopy(this.keys, newKeys, length);
        PApplet.arrayCopy(this.values, newValues, length);
        this.keys = newKeys;
        this.values = newValues;
        this.count = length;
        this.resetIndices();
    }

    public void clear()
    {
        this.count = 0;
        this.indices = new HashMap();
    }

    private void resetIndices()
    {
        this.indices = new HashMap(this.count);
        for (int i = 0; i < this.count; ++i)
        {
            this.indices.put(this.keys[i], i);
        }
    }

    public Iterable<Entry> entries()
    {
        return new Iterable<Entry>()
        {

            @Override
            public Iterator<Entry> iterator()
            {
                return DoubleDict.this.entryIterator();
            }
        };
    }

    public Iterator<Entry> entryIterator()
    {
        return new Iterator<Entry>()
        {
            int index = -1;

            @Override
            public void remove()
            {
                DoubleDict.this.removeIndex(this.index);
                --this.index;
            }

            @Override
            public Entry next()
            {
                ++this.index;
                Entry e = new Entry(DoubleDict.this.keys[this.index], DoubleDict.this.values[this.index]);
                return e;
            }

            @Override
            public boolean hasNext()
            {
                return this.index + 1 < DoubleDict.this.size();
            }
        };
    }

    public String key(int index)
    {
        return this.keys[index];
    }

    protected void crop()
    {
        if (this.count != this.keys.length)
        {
            this.keys = PApplet.subset(this.keys, 0, this.count);
            this.values = PApplet.subset(this.values, 0, this.count);
        }
    }

    public Iterable<String> keys()
    {
        return new Iterable<String>()
        {

            @Override
            public Iterator<String> iterator()
            {
                return DoubleDict.this.keyIterator();
            }
        };
    }

    public Iterator<String> keyIterator()
    {
        return new Iterator<String>()
        {
            int index = -1;

            @Override
            public void remove()
            {
                DoubleDict.this.removeIndex(this.index);
                --this.index;
            }

            @Override
            public String next()
            {
                return DoubleDict.this.key(++this.index);
            }

            @Override
            public boolean hasNext()
            {
                return this.index + 1 < DoubleDict.this.size();
            }
        };
    }

    public String[] keyArray()
    {
        this.crop();
        return this.keyArray(null);
    }

    public String[] keyArray(String[] outgoing)
    {
        if (outgoing == null || outgoing.length != this.count)
        {
            outgoing = new String[this.count];
        }
        System.arraycopy(this.keys, 0, outgoing, 0, this.count);
        return outgoing;
    }

    public double value(int index)
    {
        return this.values[index];
    }

    public Iterable<Double> values()
    {
        return new Iterable<Double>()
        {

            @Override
            public Iterator<Double> iterator()
            {
                return DoubleDict.this.valueIterator();
            }
        };
    }

    public Iterator<Double> valueIterator()
    {
        return new Iterator<Double>()
        {
            int index = -1;

            @Override
            public void remove()
            {
                DoubleDict.this.removeIndex(this.index);
                --this.index;
            }

            @Override
            public Double next()
            {
                return DoubleDict.this.value(++this.index);
            }

            @Override
            public boolean hasNext()
            {
                return this.index + 1 < DoubleDict.this.size();
            }
        };
    }

    public double[] valueArray()
    {
        this.crop();
        return this.valueArray(null);
    }

    public double[] valueArray(double[] array)
    {
        if (array == null || array.length != this.size())
        {
            array = new double[this.count];
        }
        System.arraycopy(this.values, 0, array, 0, this.count);
        return array;
    }

    public double get(String key)
    {
        int index = this.index(key);
        if (index == -1)
        {
            throw new IllegalArgumentException("No key named '" + key + "'");
        }
        return this.values[index];
    }

    public double get(String key, double alternate)
    {
        int index = this.index(key);
        if (index == -1)
        {
            return alternate;
        }
        return this.values[index];
    }

    public void set(String key, double amount)
    {
        int index = this.index(key);
        if (index == -1)
        {
            this.create(key, amount);
        }
        else
        {
            this.values[index] = amount;
        }
    }

    public void setIndex(int index, String key, double value)
    {
        if (index < 0 || index >= this.count)
        {
            throw new ArrayIndexOutOfBoundsException(index);
        }
        this.keys[index] = key;
        this.values[index] = value;
    }

    public boolean hasKey(String key)
    {
        return this.index(key) != -1;
    }

    public void add(String key, double amount)
    {
        int index = this.index(key);
        if (index == -1)
        {
            this.create(key, amount);
        }
        else
        {
            double[] arrd = this.values;
            int n = index;
            arrd[n] = arrd[n] + amount;
        }
    }

    public void sub(String key, double amount)
    {
        this.add(key, -amount);
    }

    public void mult(String key, double amount)
    {
        int index = this.index(key);
        if (index != -1)
        {
            double[] arrd = this.values;
            int n = index;
            arrd[n] = arrd[n] * amount;
        }
    }

    public void div(String key, double amount)
    {
        int index = this.index(key);
        if (index != -1)
        {
            double[] arrd = this.values;
            int n = index;
            arrd[n] = arrd[n] / amount;
        }
    }

    private void checkMinMax(String functionName)
    {
        if (this.count == 0)
        {
            String msg = String.format("Cannot use %s() on an empty %s.", functionName,
                                       this.getClass().getSimpleName());
            throw new RuntimeException(msg);
        }
    }

    public int minIndex()
    {
        if (this.count == 0)
        {
            return -1;
        }
        double m = Double.NaN;
        int mi = -1;
        for (int i = 0; i < this.count; ++i)
        {
            if (this.values[i] != this.values[i])
                continue;
            m = this.values[i];
            mi = i;
            for (int j = i + 1; j < this.count; ++j)
            {
                double d = this.values[j];
                if (d != d || !(d < m))
                    continue;
                m = this.values[j];
                mi = j;
            }
            break;
        }
        return mi;
    }

    public String minKey()
    {
        this.checkMinMax("minKey");
        int index = this.minIndex();
        if (index == -1)
        {
            return null;
        }
        return this.keys[index];
    }

    public double minValue()
    {
        this.checkMinMax("minValue");
        int index = this.minIndex();
        if (index == -1)
        {
            return Double.NaN;
        }
        return this.values[index];
    }

    public int maxIndex()
    {
        if (this.count == 0)
        {
            return -1;
        }
        double m = Double.NaN;
        int mi = -1;
        for (int i = 0; i < this.count; ++i)
        {
            if (this.values[i] != this.values[i])
                continue;
            m = this.values[i];
            mi = i;
            for (int j = i + 1; j < this.count; ++j)
            {
                double d = this.values[j];
                if (Double.isNaN(d) || !(d > m))
                    continue;
                m = this.values[j];
                mi = j;
            }
            break;
        }
        return mi;
    }

    public String maxKey()
    {
        int index = this.maxIndex();
        if (index == -1)
        {
            return null;
        }
        return this.keys[index];
    }

    public double maxValue()
    {
        int index = this.maxIndex();
        if (index == -1)
        {
            return Double.NaN;
        }
        return this.values[index];
    }

    public double sum()
    {
        double sum = 0.0;
        for (int i = 0; i < this.count; ++i)
        {
            sum += this.values[i];
        }
        return sum;
    }

    public int index(String what)
    {
        Integer found = this.indices.get(what);
        return found == null ? -1 : found;
    }

    protected void create(String what, double much)
    {
        if (this.count == this.keys.length)
        {
            this.keys = PApplet.expand(this.keys);
            this.values = PApplet.expand(this.values);
        }
        this.indices.put(what, this.count);
        this.keys[this.count] = what;
        this.values[this.count] = much;
        ++this.count;
    }

    public double remove(String key)
    {
        int index = this.index(key);
        if (index == -1)
        {
            throw new NoSuchElementException("'" + key + "' not found");
        }
        double value = this.values[index];
        this.removeIndex(index);
        return value;
    }

    public double removeIndex(int index)
    {
        if (index < 0 || index >= this.count)
        {
            throw new ArrayIndexOutOfBoundsException(index);
        }
        double value = this.values[index];
        this.indices.remove(this.keys[index]);
        for (int i = index; i < this.count - 1; ++i)
        {
            this.keys[i] = this.keys[i + 1];
            this.values[i] = this.values[i + 1];
            this.indices.put(this.keys[i], i);
        }
        --this.count;
        this.keys[this.count] = null;
        this.values[this.count] = 0.0;
        return value;
    }

    public void swap(int a, int b)
    {
        String tkey = this.keys[a];
        double tvalue = this.values[a];
        this.keys[a] = this.keys[b];
        this.values[a] = this.values[b];
        this.keys[b] = tkey;
        this.values[b] = tvalue;
    }

    public void sortKeys()
    {
        this.sortImpl(true, false, true);
    }

    public void sortKeysReverse()
    {
        this.sortImpl(true, true, true);
    }

    public void sortValues()
    {
        this.sortValues(true);
    }

    public void sortValues(boolean stable)
    {
        this.sortImpl(false, false, stable);
    }

    public void sortValuesReverse()
    {
        this.sortValuesReverse(true);
    }

    public void sortValuesReverse(boolean stable)
    {
        this.sortImpl(false, true, stable);
    }

    protected void sortImpl(final boolean useKeys, final boolean reverse, final boolean stable)
    {
        Sort s = new Sort()
        {

            @Override
            public int size()
            {
                if (useKeys)
                {
                    return DoubleDict.this.count;
                }
                if (DoubleDict.this.count == 0)
                {
                    return 0;
                }
                int right = DoubleDict.this.count - 1;
                while (DoubleDict.this.values[right] != DoubleDict.this.values[right])
                {
                    if (--right != -1)
                        continue;
                    return 0;
                }
                for (int i = right; i >= 0; --i)
                {
                    if (!Double.isNaN(DoubleDict.this.values[i]))
                        continue;
                    this.swap(i, right);
                    --right;
                }
                return right + 1;
            }

            @Override
            public int compare(int a, int b)
            {
                double diff = 0.0;
                if (useKeys)
                {
                    diff = DoubleDict.this.keys[a].compareToIgnoreCase(DoubleDict.this.keys[b]);
                    if (diff == 0.0)
                    {
                        diff = DoubleDict.this.values[a] - DoubleDict.this.values[b];
                    }
                }
                else
                {
                    diff = DoubleDict.this.values[a] - DoubleDict.this.values[b];
                    if (diff == 0.0 && stable)
                    {
                        diff = DoubleDict.this.keys[a].compareToIgnoreCase(DoubleDict.this.keys[b]);
                    }
                }
                if (diff == 0.0)
                {
                    return 0;
                }
                if (reverse)
                {
                    return diff < 0.0 ? 1 : -1;
                }
                return diff < 0.0 ? -1 : 1;
            }

            @Override
            public void swap(int a, int b)
            {
                DoubleDict.this.swap(a, b);
            }
        };
        s.run();
        this.resetIndices();
    }

    public DoubleDict getPercent()
    {
        double sum = this.sum();
        DoubleDict outgoing = new DoubleDict();
        for (int i = 0; i < this.size(); ++i)
        {
            double percent = this.value(i) / sum;
            outgoing.set(this.key(i), percent);
        }
        return outgoing;
    }

    public DoubleDict copy()
    {
        DoubleDict outgoing = new DoubleDict(this.count);
        System.arraycopy(this.keys, 0, outgoing.keys, 0, this.count);
        System.arraycopy(this.values, 0, outgoing.values, 0, this.count);
        for (int i = 0; i < this.count; ++i)
        {
            outgoing.indices.put(this.keys[i], i);
        }
        outgoing.count = this.count;
        return outgoing;
    }

    public void print()
    {
        for (int i = 0; i < this.size(); ++i)
        {
            System.out.println(this.keys[i] + " = " + this.values[i]);
        }
    }

    public void write(PrintWriter writer)
    {
        for (int i = 0; i < this.count; ++i)
        {
            writer.println(this.keys[i] + "\t" + this.values[i]);
        }
        writer.flush();
    }

    public String toJSON()
    {
        StringList items = new StringList();
        for (int i = 0; i < this.count; ++i)
        {
            items.append(JSONObject.quote(this.keys[i]) + ": " + this.values[i]);
        }
        return "{ " + items.join(", ") + " }";
    }

    public String toString()
    {
        return this.getClass().getSimpleName() + " size=" + this.size() + " " + this.toJSON();
    }

    public class Entry
    {
        public String key;
        public double value;

        Entry(String key, double value)
        {
            this.key = key;
            this.value = value;
        }
    }

}

abstract class Sort implements Runnable
{
    @Override
    public void run()
    {
        int c = this.size();
        if (c > 1)
        {
            this.sort(0, c - 1);
        }
    }

    protected void sort(int i, int j)
    {
        int pivotIndex = (i + j) / 2;
        this.swap(pivotIndex, j);
        int k = this.partition(i - 1, j);
        this.swap(k, j);
        if (k - i > 1)
        {
            this.sort(i, k - 1);
        }
        if (j - k > 1)
        {
            this.sort(k + 1, j);
        }
    }

    protected int partition(int left, int right)
    {
        int pivot = right;
        do
        {
            if (this.compare(++left, pivot) < 0)
            {
                continue;
            }
            while (right != 0 && this.compare(--right, pivot) > 0)
            {
            }
            this.swap(left, right);
            if (left >= right)
                break;
        }
        while (true);
        this.swap(left, right);
        return left;
    }

    public abstract int size();

    public abstract int compare(int var1, int var2);

    public abstract void swap(int var1, int var2);
}

class StringList implements Iterable<String>
{
    int count;
    String[] data;

    public StringList()
    {
        this(10);
    }

    public StringList(int length)
    {
        this.data = new String[length];
    }

    public StringList(String[] list)
    {
        this.count = list.length;
        this.data = new String[this.count];
        System.arraycopy(list, 0, this.data, 0, this.count);
    }

    public /* varargs */ StringList(Object... items)
    {
        this.count = items.length;
        this.data = new String[this.count];
        int index = 0;
        for (Object o : items)
        {
            if (o != null)
            {
                this.data[index] = o.toString();
            }
            ++index;
        }
    }

    public StringList(Iterable<String> iter)
    {
        this(10);
        for (String s : iter)
        {
            this.append(s);
        }
    }

    private void crop()
    {
        if (this.count != this.data.length)
        {
            this.data = PApplet.subset(this.data, 0, this.count);
        }
    }

    public int size()
    {
        return this.count;
    }

    public void resize(int length)
    {
        if (length > this.data.length)
        {
            String[] temp = new String[length];
            System.arraycopy(this.data, 0, temp, 0, this.count);
            this.data = temp;
        }
        else if (length > this.count)
        {
            Arrays.fill(this.data, this.count, length, (Object) 0);
        }
        this.count = length;
    }

    public void clear()
    {
        this.count = 0;
    }

    public String get(int index)
    {
        if (index >= this.count)
        {
            throw new ArrayIndexOutOfBoundsException(index);
        }
        return this.data[index];
    }

    public void set(int index, String what)
    {
        if (index >= this.count)
        {
            this.data = PApplet.expand(this.data, index + 1);
            for (int i = this.count; i < index; ++i)
            {
                this.data[i] = null;
            }
            this.count = index + 1;
        }
        this.data[index] = what;
    }

    public void push(String value)
    {
        this.append(value);
    }

    public String pop()
    {
        if (this.count == 0)
        {
            throw new RuntimeException("Can't call pop() on an empty list");
        }
        String value = this.get(this.count - 1);
        this.data[--this.count] = null;
        return value;
    }

    public String remove(int index)
    {
        if (index < 0 || index >= this.count)
        {
            throw new ArrayIndexOutOfBoundsException(index);
        }
        String entry = this.data[index];
        for (int i = index; i < this.count - 1; ++i)
        {
            this.data[i] = this.data[i + 1];
        }
        --this.count;
        return entry;
    }

    public int removeValue(String value)
    {
        if (value == null)
        {
            for (int i = 0; i < this.count; ++i)
            {
                if (this.data[i] != null)
                    continue;
                this.remove(i);
                return i;
            }
        }
        else
        {
            int index = this.index(value);
            if (index != -1)
            {
                this.remove(index);
                return index;
            }
        }
        return -1;
    }

    public int removeValues(String value)
    {
        int i;
        int ii = 0;
        if (value == null)
        {
            for (i = 0; i < this.count; ++i)
            {
                if (this.data[i] == null)
                    continue;
                this.data[ii++] = this.data[i];
            }
        }
        else
        {
            for (i = 0; i < this.count; ++i)
            {
                if (value.equals(this.data[i]))
                    continue;
                this.data[ii++] = this.data[i];
            }
        }
        int removed = this.count - ii;
        this.count = ii;
        return removed;
    }

    public int replaceValue(String value, String newValue)
    {
        if (value == null)
        {
            for (int i = 0; i < this.count; ++i)
            {
                if (this.data[i] != null)
                    continue;
                this.data[i] = newValue;
                return i;
            }
        }
        else
        {
            for (int i = 0; i < this.count; ++i)
            {
                if (!value.equals(this.data[i]))
                    continue;
                this.data[i] = newValue;
                return i;
            }
        }
        return -1;
    }

    public int replaceValues(String value, String newValue)
    {
        int changed;
        changed = 0;
        if (value == null)
        {
            for (int i = 0; i < this.count; ++i)
            {
                if (this.data[i] != null)
                    continue;
                this.data[i] = newValue;
                ++changed;
            }
        }
        else
        {
            for (int i = 0; i < this.count; ++i)
            {
                if (!value.equals(this.data[i]))
                    continue;
                this.data[i] = newValue;
                ++changed;
            }
        }
        return changed;
    }

    public void append(String value)
    {
        if (this.count == this.data.length)
        {
            this.data = PApplet.expand(this.data);
        }
        this.data[this.count++] = value;
    }

    public void append(String[] values)
    {
        for (String v : values)
        {
            this.append(v);
        }
    }

    public void append(StringList list)
    {
        for (String v : list.values())
        {
            this.append(v);
        }
    }

    public void appendUnique(String value)
    {
        if (!this.hasValue(value))
        {
            this.append(value);
        }
    }

    public void insert(int index, String value)
    {
        this.insert(index, new String[] { value });
    }

    public void insert(int index, String[] values)
    {
        if (index < 0)
        {
            throw new IllegalArgumentException("insert() index cannot be negative: it was " + index);
        }
        if (index >= this.data.length)
        {
            throw new IllegalArgumentException("insert() index " + index + " is past the end of this list");
        }
        String[] temp = new String[this.count + values.length];
        System.arraycopy(this.data, 0, temp, 0, Math.min(this.count, index));
        System.arraycopy(values, 0, temp, index, values.length);
        System.arraycopy(this.data, index, temp, index + values.length, this.count - index);
        this.count += values.length;
        this.data = temp;
    }

    public void insert(int index, StringList list)
    {
        this.insert(index, list.values());
    }

    public int index(String what)
    {
        if (what == null)
        {
            for (int i = 0; i < this.count; ++i)
            {
                if (this.data[i] != null)
                    continue;
                return i;
            }
        }
        else
        {
            for (int i = 0; i < this.count; ++i)
            {
                if (!what.equals(this.data[i]))
                    continue;
                return i;
            }
        }
        return -1;
    }

    public boolean hasValue(String value)
    {
        if (value == null)
        {
            for (int i = 0; i < this.count; ++i)
            {
                if (this.data[i] != null)
                    continue;
                return true;
            }
        }
        else
        {
            for (int i = 0; i < this.count; ++i)
            {
                if (!value.equals(this.data[i]))
                    continue;
                return true;
            }
        }
        return false;
    }

    public void sort()
    {
        this.sortImpl(false);
    }

    public void sortReverse()
    {
        this.sortImpl(true);
    }

    private void sortImpl(final boolean reverse)
    {
        new Sort()
        {

            @Override
            public int size()
            {
                return StringList.this.count;
            }

            @Override
            public int compare(int a, int b)
            {
                int diff = StringList.this.data[a].compareToIgnoreCase(StringList.this.data[b]);
                return reverse ? -diff : diff;
            }

            @Override
            public void swap(int a, int b)
            {
                String temp = StringList.this.data[a];
                StringList.this.data[a] = StringList.this.data[b];
                StringList.this.data[b] = temp;
            }
        } .run();
    }

    public void reverse()
    {
        int ii = this.count - 1;
        for (int i = 0; i < this.count / 2; ++i)
        {
            String t = this.data[i];
            this.data[i] = this.data[ii];
            this.data[ii] = t;
            --ii;
        }
    }

    public void shuffle()
    {
        Random r = new Random();
        int num = this.count;
        while (num > 1)
        {
            int value = r.nextInt(num);
            String temp = this.data[--num];
            this.data[num] = this.data[value];
            this.data[value] = temp;
        }
    }

    public void shuffle(PApplet sketch)
    {
        int num = this.count;
        while (num > 1)
        {
            int value = (int) sketch.random(num);
            String temp = this.data[--num];
            this.data[num] = this.data[value];
            this.data[value] = temp;
        }
    }

    public void lower()
    {
        for (int i = 0; i < this.count; ++i)
        {
            if (this.data[i] == null)
                continue;
            this.data[i] = this.data[i].toLowerCase();
        }
    }

    public void upper()
    {
        for (int i = 0; i < this.count; ++i)
        {
            if (this.data[i] == null)
                continue;
            this.data[i] = this.data[i].toUpperCase();
        }
    }

    public StringList copy()
    {
        StringList outgoing = new StringList(this.data);
        outgoing.count = this.count;
        return outgoing;
    }

    public String[] values()
    {
        this.crop();
        return this.data;
    }

    @Override
    public Iterator<String> iterator()
    {
        return new Iterator<String>()
        {
            int index = -1;

            @Override
            public void remove()
            {
                StringList.this.remove(this.index);
                --this.index;
            }

            @Override
            public String next()
            {
                return StringList.this.data[++this.index];
            }

            @Override
            public boolean hasNext()
            {
                return this.index + 1 < StringList.this.count;
            }
        };
    }

    public String[] array()
    {
        return this.array(null);
    }

    public String[] array(String[] array)
    {
        if (array == null || array.length != this.count)
        {
            array = new String[this.count];
        }
        System.arraycopy(this.data, 0, array, 0, this.count);
        return array;
    }

    public StringList getSubset(int start)
    {
        return this.getSubset(start, this.count - start);
    }

    public StringList getSubset(int start, int num)
    {
        String[] subset = new String[num];
        System.arraycopy(this.data, start, subset, 0, num);
        return new StringList(subset);
    }

    public String[] getUnique()
    {
        return this.getTally().keyArray();
    }

    public IntDict getTally()
    {
        IntDict outgoing = new IntDict();
        for (int i = 0; i < this.count; ++i)
        {
            outgoing.increment(this.data[i]);
        }
        return outgoing;
    }

    public IntDict getOrder()
    {
        IntDict outgoing = new IntDict();
        for (int i = 0; i < this.count; ++i)
        {
            outgoing.set(this.data[i], i);
        }
        return outgoing;
    }

    public String join(String separator)
    {
        if (this.count == 0)
        {
            return "";
        }
        StringBuilder sb = new StringBuilder();
        sb.append(this.data[0]);
        for (int i = 1; i < this.count; ++i)
        {
            sb.append(separator);
            sb.append(this.data[i]);
        }
        return sb.toString();
    }

    public void print()
    {
        for (int i = 0; i < this.count; ++i)
        {
            System.out.format("[%d] %s%n", i, this.data[i]);
        }
    }

    public void write(PrintWriter writer)
    {
        for (int i = 0; i < this.count; ++i)
        {
            writer.println(this.data[i]);
        }
        writer.flush();
    }

    public String toJSON()
    {
        StringList temp = new StringList();
        for (String item : this)
        {
            temp.append(JSONObject.quote(item));
        }
        return "[ " + temp.join(", ") + " ]";
    }

    public String toString()
    {
        return this.getClass().getSimpleName() + " size=" + this.size() + " " + this.toJSON();
    }

}

class FloatDict
{
    protected int count;
    protected String[] keys;
    protected float[] values;
    private HashMap<String, Integer> indices = new HashMap();

    public FloatDict()
    {
        this.count = 0;
        this.keys = new String[10];
        this.values = new float[10];
    }

    public FloatDict(int length)
    {
        this.count = 0;
        this.keys = new String[length];
        this.values = new float[length];
    }

    public FloatDict(String[] keys, float[] values)
    {
        if (keys.length != values.length)
        {
            throw new IllegalArgumentException("key and value arrays must be the same length");
        }
        this.keys = keys;
        this.values = values;
        this.count = keys.length;
        for (int i = 0; i < this.count; ++i)
        {
            this.indices.put(keys[i], i);
        }
    }

    public FloatDict(Object[][] pairs)
    {
        this.count = pairs.length;
        this.keys = new String[this.count];
        this.values = new float[this.count];
        for (int i = 0; i < this.count; ++i)
        {
            this.keys[i] = (String) pairs[i][0];
            this.values[i] = ((Float) pairs[i][1]).floatValue();
            this.indices.put(this.keys[i], i);
        }
    }

    public int size()
    {
        return this.count;
    }

    public void resize(int length)
    {
        if (length == this.count)
        {
            return;
        }
        if (length > this.count)
        {
            throw new IllegalArgumentException("resize() can only be used to shrink the dictionary");
        }
        if (length < 1)
        {
            throw new IllegalArgumentException("resize(" + length + ") is too small, use 1 or higher");
        }
        String[] newKeys = new String[length];
        float[] newValues = new float[length];
        PApplet.arrayCopy(this.keys, newKeys, length);
        PApplet.arrayCopy(this.values, newValues, length);
        this.keys = newKeys;
        this.values = newValues;
        this.count = length;
        this.resetIndices();
    }

    public void clear()
    {
        this.count = 0;
        this.indices = new HashMap();
    }

    private void resetIndices()
    {
        this.indices = new HashMap(this.count);
        for (int i = 0; i < this.count; ++i)
        {
            this.indices.put(this.keys[i], i);
        }
    }

    public Iterable<Entry> entries()
    {
        return new Iterable<Entry>()
        {

            @Override
            public Iterator<Entry> iterator()
            {
                return FloatDict.this.entryIterator();
            }
        };
    }

    public Iterator<Entry> entryIterator()
    {
        return new Iterator<Entry>()
        {
            int index = -1;

            @Override
            public void remove()
            {
                FloatDict.this.removeIndex(this.index);
                --this.index;
            }

            @Override
            public Entry next()
            {
                ++this.index;
                Entry e = new Entry(FloatDict.this.keys[this.index], FloatDict.this.values[this.index]);
                return e;
            }

            @Override
            public boolean hasNext()
            {
                return this.index + 1 < FloatDict.this.size();
            }
        };
    }

    public String key(int index)
    {
        return this.keys[index];
    }

    protected void crop()
    {
        if (this.count != this.keys.length)
        {
            this.keys = PApplet.subset(this.keys, 0, this.count);
            this.values = PApplet.subset(this.values, 0, this.count);
        }
    }

    public Iterable<String> keys()
    {
        return new Iterable<String>()
        {

            @Override
            public Iterator<String> iterator()
            {
                return FloatDict.this.keyIterator();
            }
        };
    }

    public Iterator<String> keyIterator()
    {
        return new Iterator<String>()
        {
            int index = -1;

            @Override
            public void remove()
            {
                FloatDict.this.removeIndex(this.index);
                --this.index;
            }

            @Override
            public String next()
            {
                return FloatDict.this.key(++this.index);
            }

            @Override
            public boolean hasNext()
            {
                return this.index + 1 < FloatDict.this.size();
            }
        };
    }

    public String[] keyArray()
    {
        this.crop();
        return this.keyArray(null);
    }

    public String[] keyArray(String[] outgoing)
    {
        if (outgoing == null || outgoing.length != this.count)
        {
            outgoing = new String[this.count];
        }
        System.arraycopy(this.keys, 0, outgoing, 0, this.count);
        return outgoing;
    }

    public float value(int index)
    {
        return this.values[index];
    }

    public Iterable<Float> values()
    {
        return new Iterable<Float>()
        {

            @Override
            public Iterator<Float> iterator()
            {
                return FloatDict.this.valueIterator();
            }
        };
    }

    public Iterator<Float> valueIterator()
    {
        return new Iterator<Float>()
        {
            int index = -1;

            @Override
            public void remove()
            {
                FloatDict.this.removeIndex(this.index);
                --this.index;
            }

            @Override
            public Float next()
            {
                return Float.valueOf(FloatDict.this.value(++this.index));
            }

            @Override
            public boolean hasNext()
            {
                return this.index + 1 < FloatDict.this.size();
            }
        };
    }

    public float[] valueArray()
    {
        this.crop();
        return this.valueArray(null);
    }

    public float[] valueArray(float[] array)
    {
        if (array == null || array.length != this.size())
        {
            array = new float[this.count];
        }
        System.arraycopy(this.values, 0, array, 0, this.count);
        return array;
    }

    public float get(String key)
    {
        int index = this.index(key);
        if (index == -1)
        {
            throw new IllegalArgumentException("No key named '" + key + "'");
        }
        return this.values[index];
    }

    public float get(String key, float alternate)
    {
        int index = this.index(key);
        if (index == -1)
        {
            return alternate;
        }
        return this.values[index];
    }

    public void set(String key, float amount)
    {
        int index = this.index(key);
        if (index == -1)
        {
            this.create(key, amount);
        }
        else
        {
            this.values[index] = amount;
        }
    }

    public void setIndex(int index, String key, float value)
    {
        if (index < 0 || index >= this.count)
        {
            throw new ArrayIndexOutOfBoundsException(index);
        }
        this.keys[index] = key;
        this.values[index] = value;
    }

    public boolean hasKey(String key)
    {
        return this.index(key) != -1;
    }

    public void add(String key, float amount)
    {
        int index = this.index(key);
        if (index == -1)
        {
            this.create(key, amount);
        }
        else
        {
            float[] arrf = this.values;
            int n = index;
            arrf[n] = arrf[n] + amount;
        }
    }

    public void sub(String key, float amount)
    {
        this.add(key, -amount);
    }

    public void mult(String key, float amount)
    {
        int index = this.index(key);
        if (index != -1)
        {
            float[] arrf = this.values;
            int n = index;
            arrf[n] = arrf[n] * amount;
        }
    }

    public void div(String key, float amount)
    {
        int index = this.index(key);
        if (index != -1)
        {
            float[] arrf = this.values;
            int n = index;
            arrf[n] = arrf[n] / amount;
        }
    }

    private void checkMinMax(String functionName)
    {
        if (this.count == 0)
        {
            String msg = String.format("Cannot use %s() on an empty %s.", functionName,
                                       this.getClass().getSimpleName());
            throw new RuntimeException(msg);
        }
    }

    public int minIndex()
    {
        if (this.count == 0)
        {
            return -1;
        }
        float m = Float.NaN;
        int mi = -1;
        for (int i = 0; i < this.count; ++i)
        {
            if (this.values[i] != this.values[i])
                continue;
            m = this.values[i];
            mi = i;
            for (int j = i + 1; j < this.count; ++j)
            {
                float d = this.values[j];
                if (d != d || !(d < m))
                    continue;
                m = this.values[j];
                mi = j;
            }
            break;
        }
        return mi;
    }

    public String minKey()
    {
        this.checkMinMax("minKey");
        int index = this.minIndex();
        if (index == -1)
        {
            return null;
        }
        return this.keys[index];
    }

    public float minValue()
    {
        this.checkMinMax("minValue");
        int index = this.minIndex();
        if (index == -1)
        {
            return Float.NaN;
        }
        return this.values[index];
    }

    public int maxIndex()
    {
        if (this.count == 0)
        {
            return -1;
        }
        float m = Float.NaN;
        int mi = -1;
        for (int i = 0; i < this.count; ++i)
        {
            if (this.values[i] != this.values[i])
                continue;
            m = this.values[i];
            mi = i;
            for (int j = i + 1; j < this.count; ++j)
            {
                float d = this.values[j];
                if (Float.isNaN(d) || !(d > m))
                    continue;
                m = this.values[j];
                mi = j;
            }
            break;
        }
        return mi;
    }

    public String maxKey()
    {
        int index = this.maxIndex();
        if (index == -1)
        {
            return null;
        }
        return this.keys[index];
    }

    public float maxValue()
    {
        int index = this.maxIndex();
        if (index == -1)
        {
            return Float.NaN;
        }
        return this.values[index];
    }

    public float sum()
    {
        double amount = this.sumDouble();
        if (amount > 3.4028234663852886E38)
        {
            throw new RuntimeException("sum() exceeds 3.4028235E38, use sumDouble()");
        }
        if (amount < -3.4028234663852886E38)
        {
            throw new RuntimeException("sum() lower than -3.4028235E38, use sumDouble()");
        }
        return (float) amount;
    }

    public double sumDouble()
    {
        double sum = 0.0;
        for (int i = 0; i < this.count; ++i)
        {
            sum += (double) this.values[i];
        }
        return sum;
    }

    public int index(String what)
    {
        Integer found = this.indices.get(what);
        return found == null ? -1 : found;
    }

    protected void create(String what, float much)
    {
        if (this.count == this.keys.length)
        {
            this.keys = PApplet.expand(this.keys);
            this.values = PApplet.expand(this.values);
        }
        this.indices.put(what, this.count);
        this.keys[this.count] = what;
        this.values[this.count] = much;
        ++this.count;
    }

    public float remove(String key)
    {
        int index = this.index(key);
        if (index == -1)
        {
            throw new NoSuchElementException("'" + key + "' not found");
        }
        float value = this.values[index];
        this.removeIndex(index);
        return value;
    }

    public float removeIndex(int index)
    {
        if (index < 0 || index >= this.count)
        {
            throw new ArrayIndexOutOfBoundsException(index);
        }
        float value = this.values[index];
        this.indices.remove(this.keys[index]);
        for (int i = index; i < this.count - 1; ++i)
        {
            this.keys[i] = this.keys[i + 1];
            this.values[i] = this.values[i + 1];
            this.indices.put(this.keys[i], i);
        }
        --this.count;
        this.keys[this.count] = null;
        this.values[this.count] = 0.0f;
        return value;
    }

    public void swap(int a, int b)
    {
        String tkey = this.keys[a];
        float tvalue = this.values[a];
        this.keys[a] = this.keys[b];
        this.values[a] = this.values[b];
        this.keys[b] = tkey;
        this.values[b] = tvalue;
    }

    public void sortKeys()
    {
        this.sortImpl(true, false, true);
    }

    public void sortKeysReverse()
    {
        this.sortImpl(true, true, true);
    }

    public void sortValues()
    {
        this.sortValues(true);
    }

    public void sortValues(boolean stable)
    {
        this.sortImpl(false, false, stable);
    }

    public void sortValuesReverse()
    {
        this.sortValuesReverse(true);
    }

    public void sortValuesReverse(boolean stable)
    {
        this.sortImpl(false, true, stable);
    }

    protected void sortImpl(final boolean useKeys, final boolean reverse, final boolean stable)
    {
        Sort s = new Sort()
        {

            @Override
            public int size()
            {
                if (useKeys)
                {
                    return FloatDict.this.count;
                }
                if (FloatDict.this.count == 0)
                {
                    return 0;
                }
                int right = FloatDict.this.count - 1;
                while (FloatDict.this.values[right] != FloatDict.this.values[right])
                {
                    if (--right != -1)
                        continue;
                    return 0;
                }
                for (int i = right; i >= 0; --i)
                {
                    if (!Float.isNaN(FloatDict.this.values[i]))
                        continue;
                    this.swap(i, right);
                    --right;
                }
                return right + 1;
            }

            @Override
            public int compare(int a, int b)
            {
                float diff = 0.0f;
                if (useKeys)
                {
                    diff = FloatDict.this.keys[a].compareToIgnoreCase(FloatDict.this.keys[b]);
                    if (diff == 0.0f)
                    {
                        diff = FloatDict.this.values[a] - FloatDict.this.values[b];
                    }
                }
                else
                {
                    diff = FloatDict.this.values[a] - FloatDict.this.values[b];
                    if (diff == 0.0f && stable)
                    {
                        diff = FloatDict.this.keys[a].compareToIgnoreCase(FloatDict.this.keys[b]);
                    }
                }
                if (diff == 0.0f)
                {
                    return 0;
                }
                if (reverse)
                {
                    return diff < 0.0f ? 1 : -1;
                }
                return diff < 0.0f ? -1 : 1;
            }

            @Override
            public void swap(int a, int b)
            {
                FloatDict.this.swap(a, b);
            }
        };
        s.run();
        this.resetIndices();
    }

    public FloatDict getPercent()
    {
        double sum = this.sum();
        FloatDict outgoing = new FloatDict();
        for (int i = 0; i < this.size(); ++i)
        {
            double percent = (double) this.value(i) / sum;
            outgoing.set(this.key(i), (float) percent);
        }
        return outgoing;
    }

    public FloatDict copy()
    {
        FloatDict outgoing = new FloatDict(this.count);
        System.arraycopy(this.keys, 0, outgoing.keys, 0, this.count);
        System.arraycopy(this.values, 0, outgoing.values, 0, this.count);
        for (int i = 0; i < this.count; ++i)
        {
            outgoing.indices.put(this.keys[i], i);
        }
        outgoing.count = this.count;
        return outgoing;
    }

    public void print()
    {
        for (int i = 0; i < this.size(); ++i)
        {
            System.out.println(this.keys[i] + " = " + this.values[i]);
        }
    }

    public void write(PrintWriter writer)
    {
        for (int i = 0; i < this.count; ++i)
        {
            writer.println(this.keys[i] + "\t" + this.values[i]);
        }
        writer.flush();
    }

    public String toJSON()
    {
        StringList items = new StringList();
        for (int i = 0; i < this.count; ++i)
        {
            items.append(JSONObject.quote(this.keys[i]) + ": " + this.values[i]);
        }
        return "{ " + items.join(", ") + " }";
    }

    public String toString()
    {
        return this.getClass().getSimpleName() + " size=" + this.size() + " " + this.toJSON();
    }

    public class Entry
    {
        public String key;
        public float value;

        Entry(String key, float value)
        {
            this.key = key;
            this.value = value;
        }
    }

}

class FloatList implements Iterable<Float>
{
    int count;
    float[] data;

    public FloatList()
    {
        this.data = new float[10];
    }

    public FloatList(int length)
    {
        this.data = new float[length];
    }

    public FloatList(float[] list)
    {
        this.count = list.length;
        this.data = new float[this.count];
        System.arraycopy(list, 0, this.data, 0, this.count);
    }

    public FloatList(Iterable<Object> iter)
    {
        this(10);
        for (Object o : iter)
        {
            if (o == null)
            {
                this.append(Float.NaN);
                continue;
            }
            if (o instanceof Number)
            {
                this.append(((Number) o).floatValue());
                continue;
            }
            this.append(PApplet.parseFloat(o.toString().trim()));
        }
        this.crop();
    }

    public /* varargs */ FloatList(Object... items)
    {
        float missingValue = Float.NaN;
        this.count = items.length;
        this.data = new float[this.count];
        int index = 0;
        for (Object o : items)
        {
            float value = Float.NaN;
            if (o != null)
            {
                value = o instanceof Number ? ((Number) o).floatValue()
                        : PApplet.parseFloat(o.toString().trim(), Float.NaN);
            }
            this.data[index++] = value;
        }
    }

    private void crop()
    {
        if (this.count != this.data.length)
        {
            this.data = PApplet.subset(this.data, 0, this.count);
        }
    }

    public int size()
    {
        return this.count;
    }

    public void resize(int length)
    {
        if (length > this.data.length)
        {
            float[] temp = new float[length];
            System.arraycopy(this.data, 0, temp, 0, this.count);
            this.data = temp;
        }
        else if (length > this.count)
        {
            Arrays.fill(this.data, this.count, length, 0.0f);
        }
        this.count = length;
    }

    public void clear()
    {
        this.count = 0;
    }

    public float get(int index)
    {
        if (index >= this.count)
        {
            throw new ArrayIndexOutOfBoundsException(index);
        }
        return this.data[index];
    }

    public void set(int index, float what)
    {
        if (index >= this.count)
        {
            this.data = PApplet.expand(this.data, index + 1);
            for (int i = this.count; i < index; ++i)
            {
                this.data[i] = 0.0f;
            }
            this.count = index + 1;
        }
        this.data[index] = what;
    }

    public void push(float value)
    {
        this.append(value);
    }

    public float pop()
    {
        if (this.count == 0)
        {
            throw new RuntimeException("Can't call pop() on an empty list");
        }
        float value = this.get(this.count - 1);
        --this.count;
        return value;
    }

    public float remove(int index)
    {
        if (index < 0 || index >= this.count)
        {
            throw new ArrayIndexOutOfBoundsException(index);
        }
        float entry = this.data[index];
        for (int i = index; i < this.count - 1; ++i)
        {
            this.data[i] = this.data[i + 1];
        }
        --this.count;
        return entry;
    }

    public int removeValue(int value)
    {
        int index = this.index(value);
        if (index != -1)
        {
            this.remove(index);
            return index;
        }
        return -1;
    }

    public int removeValues(int value)
    {
        int i;
        int ii = 0;
        if (Float.isNaN(value))
        {
            for (i = 0; i < this.count; ++i)
            {
                if (Float.isNaN(this.data[i]))
                    continue;
                this.data[ii++] = this.data[i];
            }
        }
        else
        {
            for (i = 0; i < this.count; ++i)
            {
                if (this.data[i] == (float) value)
                    continue;
                this.data[ii++] = this.data[i];
            }
        }
        int removed = this.count - ii;
        this.count = ii;
        return removed;
    }

    public boolean replaceValue(float value, float newValue)
    {
        if (Float.isNaN(value))
        {
            for (int i = 0; i < this.count; ++i)
            {
                if (!Float.isNaN(this.data[i]))
                    continue;
                this.data[i] = newValue;
                return true;
            }
        }
        else
        {
            int index = this.index(value);
            if (index != -1)
            {
                this.data[index] = newValue;
                return true;
            }
        }
        return false;
    }

    public boolean replaceValues(float value, float newValue)
    {
        boolean changed;
        changed = false;
        if (Float.isNaN(value))
        {
            for (int i = 0; i < this.count; ++i)
            {
                if (!Float.isNaN(this.data[i]))
                    continue;
                this.data[i] = newValue;
                changed = true;
            }
        }
        else
        {
            for (int i = 0; i < this.count; ++i)
            {
                if (this.data[i] != value)
                    continue;
                this.data[i] = newValue;
                changed = true;
            }
        }
        return changed;
    }

    public void append(float value)
    {
        if (this.count == this.data.length)
        {
            this.data = PApplet.expand(this.data);
        }
        this.data[this.count++] = value;
    }

    public void append(float[] values)
    {
        for (float v : values)
        {
            this.append(v);
        }
    }

    public void append(FloatList list)
    {
        for (float v : list.values())
        {
            this.append(v);
        }
    }

    public void appendUnique(float value)
    {
        if (!this.hasValue(value))
        {
            this.append(value);
        }
    }

    public void insert(int index, float value)
    {
        this.insert(index, new float[] { value });
    }

    public void insert(int index, float[] values)
    {
        if (index < 0)
        {
            throw new IllegalArgumentException("insert() index cannot be negative: it was " + index);
        }
        if (index >= this.data.length)
        {
            throw new IllegalArgumentException("insert() index " + index + " is past the end of this list");
        }
        float[] temp = new float[this.count + values.length];
        System.arraycopy(this.data, 0, temp, 0, Math.min(this.count, index));
        System.arraycopy(values, 0, temp, index, values.length);
        System.arraycopy(this.data, index, temp, index + values.length, this.count - index);
        this.count += values.length;
        this.data = temp;
    }

    public void insert(int index, FloatList list)
    {
        this.insert(index, list.values());
    }

    public int index(float what)
    {
        for (int i = 0; i < this.count; ++i)
        {
            if (this.data[i] != what)
                continue;
            return i;
        }
        return -1;
    }

    public boolean hasValue(float value)
    {
        if (Float.isNaN(value))
        {
            for (int i = 0; i < this.count; ++i)
            {
                if (!Float.isNaN(this.data[i]))
                    continue;
                return true;
            }
        }
        else
        {
            for (int i = 0; i < this.count; ++i)
            {
                if (this.data[i] != value)
                    continue;
                return true;
            }
        }
        return false;
    }

    private void boundsProblem(int index, String method)
    {
        String msg = String.format("The list size is %d. You cannot %s() to element %d.", this.count, method, index);
        throw new ArrayIndexOutOfBoundsException(msg);
    }

    public void add(int index, float amount)
    {
        if (index < this.count)
        {
            float[] arrf = this.data;
            int n = index;
            arrf[n] = arrf[n] + amount;
        }
        else
        {
            this.boundsProblem(index, "add");
        }
    }

    public void sub(int index, float amount)
    {
        if (index < this.count)
        {
            float[] arrf = this.data;
            int n = index;
            arrf[n] = arrf[n] - amount;
        }
        else
        {
            this.boundsProblem(index, "sub");
        }
    }

    public void mult(int index, float amount)
    {
        if (index < this.count)
        {
            float[] arrf = this.data;
            int n = index;
            arrf[n] = arrf[n] * amount;
        }
        else
        {
            this.boundsProblem(index, "mult");
        }
    }

    public void div(int index, float amount)
    {
        if (index < this.count)
        {
            float[] arrf = this.data;
            int n = index;
            arrf[n] = arrf[n] / amount;
        }
        else
        {
            this.boundsProblem(index, "div");
        }
    }

    private void checkMinMax(String functionName)
    {
        if (this.count == 0)
        {
            String msg = String.format("Cannot use %s() on an empty %s.", functionName,
                                       this.getClass().getSimpleName());
            throw new RuntimeException(msg);
        }
    }

    public float min()
    {
        this.checkMinMax("min");
        int index = this.minIndex();
        return index == -1 ? Float.NaN : this.data[index];
    }

    public int minIndex()
    {
        this.checkMinMax("minIndex");
        float m = Float.NaN;
        int mi = -1;
        for (int i = 0; i < this.count; ++i)
        {
            if (this.data[i] != this.data[i])
                continue;
            m = this.data[i];
            mi = i;
            for (int j = i + 1; j < this.count; ++j)
            {
                float d = this.data[j];
                if (Float.isNaN(d) || !(d < m))
                    continue;
                m = this.data[j];
                mi = j;
            }
            break;
        }
        return mi;
    }

    public float max()
    {
        this.checkMinMax("max");
        int index = this.maxIndex();
        return index == -1 ? Float.NaN : this.data[index];
    }

    public int maxIndex()
    {
        this.checkMinMax("maxIndex");
        float m = Float.NaN;
        int mi = -1;
        for (int i = 0; i < this.count; ++i)
        {
            if (this.data[i] != this.data[i])
                continue;
            m = this.data[i];
            mi = i;
            for (int j = i + 1; j < this.count; ++j)
            {
                float d = this.data[j];
                if (Float.isNaN(d) || !(d > m))
                    continue;
                m = this.data[j];
                mi = j;
            }
            break;
        }
        return mi;
    }

    public float sum()
    {
        double amount = this.sumDouble();
        if (amount > 3.4028234663852886E38)
        {
            throw new RuntimeException("sum() exceeds 3.4028235E38, use sumDouble()");
        }
        if (amount < -3.4028234663852886E38)
        {
            throw new RuntimeException("sum() lower than -3.4028235E38, use sumDouble()");
        }
        return (float) amount;
    }

    public double sumDouble()
    {
        double sum = 0.0;
        for (int i = 0; i < this.count; ++i)
        {
            sum += (double) this.data[i];
        }
        return sum;
    }

    public void sort()
    {
        Arrays.sort(this.data, 0, this.count);
    }

    public void sortReverse()
    {
        new Sort()
        {

            @Override
            public int size()
            {
                if (FloatList.this.count == 0)
                {
                    return 0;
                }
                int right = FloatList.this.count - 1;
                while (FloatList.this.data[right] != FloatList.this.data[right])
                {
                    if (--right != -1)
                        continue;
                    return 0;
                }
                for (int i = right; i >= 0; --i)
                {
                    float v = FloatList.this.data[i];
                    if (v == v)
                        continue;
                    FloatList.this.data[i] = FloatList.this.data[right];
                    FloatList.this.data[right] = v;
                    --right;
                }
                return right + 1;
            }

            @Override
            public int compare(int a, int b)
            {
                float diff = FloatList.this.data[b] - FloatList.this.data[a];
                return diff == 0.0f ? 0 : (diff < 0.0f ? -1 : 1);
            }

            @Override
            public void swap(int a, int b)
            {
                float temp = FloatList.this.data[a];
                FloatList.this.data[a] = FloatList.this.data[b];
                FloatList.this.data[b] = temp;
            }
        } .run();
    }

    public void reverse()
    {
        int ii = this.count - 1;
        for (int i = 0; i < this.count / 2; ++i)
        {
            float t = this.data[i];
            this.data[i] = this.data[ii];
            this.data[ii] = t;
            --ii;
        }
    }

    public void shuffle()
    {
        Random r = new Random();
        int num = this.count;
        while (num > 1)
        {
            int value = r.nextInt(num);
            float temp = this.data[--num];
            this.data[num] = this.data[value];
            this.data[value] = temp;
        }
    }

    public void shuffle(PApplet sketch)
    {
        int num = this.count;
        while (num > 1)
        {
            int value = (int) sketch.random(num);
            float temp = this.data[--num];
            this.data[num] = this.data[value];
            this.data[value] = temp;
        }
    }

    public FloatList copy()
    {
        FloatList outgoing = new FloatList(this.data);
        outgoing.count = this.count;
        return outgoing;
    }

    public float[] values()
    {
        this.crop();
        return this.data;
    }

    @Override
    public Iterator<Float> iterator()
    {
        return new Iterator<Float>()
        {
            int index = -1;

            @Override
            public void remove()
            {
                FloatList.this.remove(this.index);
                --this.index;
            }

            @Override
            public Float next()
            {
                return Float.valueOf(FloatList.this.data[++this.index]);
            }

            @Override
            public boolean hasNext()
            {
                return this.index + 1 < FloatList.this.count;
            }
        };
    }

    public float[] array()
    {
        return this.array(null);
    }

    public float[] array(float[] array)
    {
        if (array == null || array.length != this.count)
        {
            array = new float[this.count];
        }
        System.arraycopy(this.data, 0, array, 0, this.count);
        return array;
    }

    public FloatList getPercent()
    {
        double sum = 0.0;
        for (float value : this.array())
        {
            sum += (double) value;
        }
        FloatList outgoing = new FloatList(this.count);
        for (int i = 0; i < this.count; ++i)
        {
            double percent = (double) this.data[i] / sum;
            outgoing.set(i, (float) percent);
        }
        return outgoing;
    }

    public FloatList getSubset(int start)
    {
        return this.getSubset(start, this.count - start);
    }

    public FloatList getSubset(int start, int num)
    {
        float[] subset = new float[num];
        System.arraycopy(this.data, start, subset, 0, num);
        return new FloatList(subset);
    }

    public String join(String separator)
    {
        if (this.count == 0)
        {
            return "";
        }
        StringBuilder sb = new StringBuilder();
        sb.append(this.data[0]);
        for (int i = 1; i < this.count; ++i)
        {
            sb.append(separator);
            sb.append(this.data[i]);
        }
        return sb.toString();
    }

    public void print()
    {
        for (int i = 0; i < this.count; ++i)
        {
            System.out.format("[%d] %f%n", i, Float.valueOf(this.data[i]));
        }
    }

    public void write(PrintWriter writer)
    {
        for (int i = 0; i < this.count; ++i)
        {
            writer.println(this.data[i]);
        }
        writer.flush();
    }

    public String toJSON()
    {
        return "[ " + this.join(", ") + " ]";
    }

    public String toString()
    {
        return this.getClass().getSimpleName() + " size=" + this.size() + " " + this.toJSON();
    }

}

class IntDict
{
    protected int count;
    protected String[] keys;
    protected int[] values;
    private HashMap<String, Integer> indices = new HashMap();

    public IntDict()
    {
        this.count = 0;
        this.keys = new String[10];
        this.values = new int[10];
    }

    public IntDict(int length)
    {
        this.count = 0;
        this.keys = new String[length];
        this.values = new int[length];
    }

    public IntDict(String[] keys, int[] values)
    {
        if (keys.length != values.length)
        {
            throw new IllegalArgumentException("key and value arrays must be the same length");
        }
        this.keys = keys;
        this.values = values;
        this.count = keys.length;
        for (int i = 0; i < this.count; ++i)
        {
            this.indices.put(keys[i], i);
        }
    }

    public IntDict(Object[][] pairs)
    {
        this.count = pairs.length;
        this.keys = new String[this.count];
        this.values = new int[this.count];
        for (int i = 0; i < this.count; ++i)
        {
            this.keys[i] = (String) pairs[i][0];
            this.values[i] = (Integer) pairs[i][1];
            this.indices.put(this.keys[i], i);
        }
    }

    public int size()
    {
        return this.count;
    }

    public void resize(int length)
    {
        if (length > this.count)
        {
            throw new IllegalArgumentException("resize() can only be used to shrink the dictionary");
        }
        if (length < 1)
        {
            throw new IllegalArgumentException("resize(" + length + ") is too small, use 1 or higher");
        }
        String[] newKeys = new String[length];
        int[] newValues = new int[length];
        PApplet.arrayCopy(this.keys, newKeys, length);
        PApplet.arrayCopy(this.values, newValues, length);
        this.keys = newKeys;
        this.values = newValues;
        this.count = length;
        this.resetIndices();
    }

    public void clear()
    {
        this.count = 0;
        this.indices = new HashMap();
    }

    private void resetIndices()
    {
        this.indices = new HashMap(this.count);
        for (int i = 0; i < this.count; ++i)
        {
            this.indices.put(this.keys[i], i);
        }
    }

    public Iterable<Entry> entries()
    {
        return new Iterable<Entry>()
        {

            @Override
            public Iterator<Entry> iterator()
            {
                return IntDict.this.entryIterator();
            }
        };
    }

    public Iterator<Entry> entryIterator()
    {
        return new Iterator<Entry>()
        {
            int index = -1;

            @Override
            public void remove()
            {
                IntDict.this.removeIndex(this.index);
                --this.index;
            }

            @Override
            public Entry next()
            {
                ++this.index;
                Entry e = new Entry(IntDict.this.keys[this.index], IntDict.this.values[this.index]);
                return e;
            }

            @Override
            public boolean hasNext()
            {
                return this.index + 1 < IntDict.this.size();
            }
        };
    }

    public String key(int index)
    {
        return this.keys[index];
    }

    protected void crop()
    {
        if (this.count != this.keys.length)
        {
            this.keys = PApplet.subset(this.keys, 0, this.count);
            this.values = PApplet.subset(this.values, 0, this.count);
        }
    }

    public Iterable<String> keys()
    {
        return new Iterable<String>()
        {

            @Override
            public Iterator<String> iterator()
            {
                return IntDict.this.keyIterator();
            }
        };
    }

    public Iterator<String> keyIterator()
    {
        return new Iterator<String>()
        {
            int index = -1;

            @Override
            public void remove()
            {
                IntDict.this.removeIndex(this.index);
                --this.index;
            }

            @Override
            public String next()
            {
                return IntDict.this.key(++this.index);
            }

            @Override
            public boolean hasNext()
            {
                return this.index + 1 < IntDict.this.size();
            }
        };
    }

    public String[] keyArray()
    {
        this.crop();
        return this.keyArray(null);
    }

    public String[] keyArray(String[] outgoing)
    {
        if (outgoing == null || outgoing.length != this.count)
        {
            outgoing = new String[this.count];
        }
        System.arraycopy(this.keys, 0, outgoing, 0, this.count);
        return outgoing;
    }

    public int value(int index)
    {
        return this.values[index];
    }

    public Iterable<Integer> values()
    {
        return new Iterable<Integer>()
        {

            @Override
            public Iterator<Integer> iterator()
            {
                return IntDict.this.valueIterator();
            }
        };
    }

    public Iterator<Integer> valueIterator()
    {
        return new Iterator<Integer>()
        {
            int index = -1;

            @Override
            public void remove()
            {
                IntDict.this.removeIndex(this.index);
                --this.index;
            }

            @Override
            public Integer next()
            {
                return IntDict.this.value(++this.index);
            }

            @Override
            public boolean hasNext()
            {
                return this.index + 1 < IntDict.this.size();
            }
        };
    }

    public int[] valueArray()
    {
        this.crop();
        return this.valueArray(null);
    }

    public int[] valueArray(int[] array)
    {
        if (array == null || array.length != this.size())
        {
            array = new int[this.count];
        }
        System.arraycopy(this.values, 0, array, 0, this.count);
        return array;
    }

    public int get(String key)
    {
        int index = this.index(key);
        if (index == -1)
        {
            throw new IllegalArgumentException("No key named '" + key + "'");
        }
        return this.values[index];
    }

    public int get(String key, int alternate)
    {
        int index = this.index(key);
        if (index == -1)
        {
            return alternate;
        }
        return this.values[index];
    }

    public void set(String key, int amount)
    {
        int index = this.index(key);
        if (index == -1)
        {
            this.create(key, amount);
        }
        else
        {
            this.values[index] = amount;
        }
    }

    public void setIndex(int index, String key, int value)
    {
        if (index < 0 || index >= this.count)
        {
            throw new ArrayIndexOutOfBoundsException(index);
        }
        this.keys[index] = key;
        this.values[index] = value;
    }

    public boolean hasKey(String key)
    {
        return this.index(key) != -1;
    }

    public void increment(String key)
    {
        this.add(key, 1);
    }

    public void increment(IntDict dict)
    {
        for (int i = 0; i < dict.count; ++i)
        {
            this.add(dict.key(i), dict.value(i));
        }
    }

    public void add(String key, int amount)
    {
        int index = this.index(key);
        if (index == -1)
        {
            this.create(key, amount);
        }
        else
        {
            int[] arrn = this.values;
            int n = index;
            arrn[n] = arrn[n] + amount;
        }
    }

    public void sub(String key, int amount)
    {
        this.add(key, -amount);
    }

    public void mult(String key, int amount)
    {
        int index = this.index(key);
        if (index != -1)
        {
            int[] arrn = this.values;
            int n = index;
            arrn[n] = arrn[n] * amount;
        }
    }

    public void div(String key, int amount)
    {
        int index = this.index(key);
        if (index != -1)
        {
            int[] arrn = this.values;
            int n = index;
            arrn[n] = arrn[n] / amount;
        }
    }

    private void checkMinMax(String functionName)
    {
        if (this.count == 0)
        {
            String msg = String.format("Cannot use %s() on an empty %s.", functionName,
                                       this.getClass().getSimpleName());
            throw new RuntimeException(msg);
        }
    }

    public int minIndex()
    {
        if (this.count == 0)
        {
            return -1;
        }
        int index = 0;
        int value = this.values[0];
        for (int i = 1; i < this.count; ++i)
        {
            if (this.values[i] >= value)
                continue;
            index = i;
            value = this.values[i];
        }
        return index;
    }

    public String minKey()
    {
        this.checkMinMax("minKey");
        int index = this.minIndex();
        if (index == -1)
        {
            return null;
        }
        return this.keys[index];
    }

    public int minValue()
    {
        this.checkMinMax("minValue");
        return this.values[this.minIndex()];
    }

    public int maxIndex()
    {
        if (this.count == 0)
        {
            return -1;
        }
        int index = 0;
        int value = this.values[0];
        for (int i = 1; i < this.count; ++i)
        {
            if (this.values[i] <= value)
                continue;
            index = i;
            value = this.values[i];
        }
        return index;
    }

    public String maxKey()
    {
        int index = this.maxIndex();
        if (index == -1)
        {
            return null;
        }
        return this.keys[index];
    }

    public int maxValue()
    {
        this.checkMinMax("maxIndex");
        return this.values[this.maxIndex()];
    }

    public int sum()
    {
        long amount = this.sumLong();
        if (amount > Integer.MAX_VALUE)
        {
            throw new RuntimeException("sum() exceeds 2147483647, use sumLong()");
        }
        if (amount < Integer.MIN_VALUE)
        {
            throw new RuntimeException("sum() less than -2147483648, use sumLong()");
        }
        return (int) amount;
    }

    public long sumLong()
    {
        long sum = 0L;
        for (int i = 0; i < this.count; ++i)
        {
            sum += (long) this.values[i];
        }
        return sum;
    }

    public int index(String what)
    {
        Integer found = this.indices.get(what);
        return found == null ? -1 : found;
    }

    protected void create(String what, int much)
    {
        if (this.count == this.keys.length)
        {
            this.keys = PApplet.expand(this.keys);
            this.values = PApplet.expand(this.values);
        }
        this.indices.put(what, this.count);
        this.keys[this.count] = what;
        this.values[this.count] = much;
        ++this.count;
    }

    public int remove(String key)
    {
        int index = this.index(key);
        if (index == -1)
        {
            throw new NoSuchElementException("'" + key + "' not found");
        }
        int value = this.values[index];
        this.removeIndex(index);
        return value;
    }

    public int removeIndex(int index)
    {
        if (index < 0 || index >= this.count)
        {
            throw new ArrayIndexOutOfBoundsException(index);
        }
        int value = this.values[index];
        this.indices.remove(this.keys[index]);
        for (int i = index; i < this.count - 1; ++i)
        {
            this.keys[i] = this.keys[i + 1];
            this.values[i] = this.values[i + 1];
            this.indices.put(this.keys[i], i);
        }
        --this.count;
        this.keys[this.count] = null;
        this.values[this.count] = 0;
        return value;
    }

    public void swap(int a, int b)
    {
        String tkey = this.keys[a];
        int tvalue = this.values[a];
        this.keys[a] = this.keys[b];
        this.values[a] = this.values[b];
        this.keys[b] = tkey;
        this.values[b] = tvalue;
    }

    public void sortKeys()
    {
        this.sortImpl(true, false, true);
    }

    public void sortKeysReverse()
    {
        this.sortImpl(true, true, true);
    }

    public void sortValues()
    {
        this.sortValues(true);
    }

    public void sortValues(boolean stable)
    {
        this.sortImpl(false, false, stable);
    }

    public void sortValuesReverse()
    {
        this.sortValuesReverse(true);
    }

    public void sortValuesReverse(boolean stable)
    {
        this.sortImpl(false, true, stable);
    }

    protected void sortImpl(final boolean useKeys, final boolean reverse, final boolean stable)
    {
        Sort s = new Sort()
        {

            @Override
            public int size()
            {
                return IntDict.this.count;
            }

            @Override
            public int compare(int a, int b)
            {
                int diff = 0;
                if (useKeys)
                {
                    diff = IntDict.this.keys[a].compareToIgnoreCase(IntDict.this.keys[b]);
                    if (diff == 0)
                    {
                        diff = IntDict.this.values[a] - IntDict.this.values[b];
                    }
                }
                else
                {
                    diff = IntDict.this.values[a] - IntDict.this.values[b];
                    if (diff == 0 && stable)
                    {
                        diff = IntDict.this.keys[a].compareToIgnoreCase(IntDict.this.keys[b]);
                    }
                }
                return reverse ? -diff : diff;
            }

            @Override
            public void swap(int a, int b)
            {
                IntDict.this.swap(a, b);
            }
        };
        s.run();
        this.resetIndices();
    }

    public FloatDict getPercent()
    {
        double sum = this.sum();
        FloatDict outgoing = new FloatDict();
        for (int i = 0; i < this.size(); ++i)
        {
            double percent = (double) this.value(i) / sum;
            outgoing.set(this.key(i), (float) percent);
        }
        return outgoing;
    }

    public IntDict copy()
    {
        IntDict outgoing = new IntDict(this.count);
        System.arraycopy(this.keys, 0, outgoing.keys, 0, this.count);
        System.arraycopy(this.values, 0, outgoing.values, 0, this.count);
        for (int i = 0; i < this.count; ++i)
        {
            outgoing.indices.put(this.keys[i], i);
        }
        outgoing.count = this.count;
        return outgoing;
    }

    public void print()
    {
        for (int i = 0; i < this.size(); ++i)
        {
            System.out.println(this.keys[i] + " = " + this.values[i]);
        }
    }

    public void write(PrintWriter writer)
    {
        for (int i = 0; i < this.count; ++i)
        {
            writer.println(this.keys[i] + "\t" + this.values[i]);
        }
        writer.flush();
    }

    public String toJSON()
    {
        StringList items = new StringList();
        for (int i = 0; i < this.count; ++i)
        {
            items.append(JSONObject.quote(this.keys[i]) + ": " + this.values[i]);
        }
        return "{ " + items.join(", ") + " }";
    }

    public String toString()
    {
        return this.getClass().getSimpleName() + " size=" + this.size() + " " + this.toJSON();
    }

    public class Entry
    {
        public String key;
        public int value;

        Entry(String key, int value)
        {
            this.key = key;
            this.value = value;
        }
    }

}

class IntList implements Iterable<Integer>
{
    protected int count;
    protected int[] data;

    public IntList()
    {
        this.data = new int[10];
    }

    public IntList(int length)
    {
        this.data = new int[length];
    }

    public IntList(int[] source)
    {
        this.count = source.length;
        this.data = new int[this.count];
        System.arraycopy(source, 0, this.data, 0, this.count);
    }

    public IntList(Iterable<Object> iter)
    {
        this(10);
        for (Object o : iter)
        {
            if (o == null)
            {
                this.append(0);
                continue;
            }
            if (o instanceof Number)
            {
                this.append(((Number) o).intValue());
                continue;
            }
            this.append(PApplet.parseInt(o.toString().trim()));
        }
        this.crop();
    }

    public /* varargs */ IntList(Object... items)
    {
        boolean missingValue = false;
        this.count = items.length;
        this.data = new int[this.count];
        int index = 0;
        for (Object o : items)
        {
            int value = 0;
            if (o != null)
            {
                value = o instanceof Number ? ((Number) o).intValue() : PApplet.parseInt(o.toString().trim(), 0);
            }
            this.data[index++] = value;
        }
    }

    public static IntList fromRange(int stop)
    {
        return IntList.fromRange(0, stop);
    }

    public static IntList fromRange(int start, int stop)
    {
        int count = stop - start;
        IntList newbie = new IntList(count);
        for (int i = 0; i < count; ++i)
        {
            newbie.set(i, start + i);
        }
        return newbie;
    }

    private void crop()
    {
        if (this.count != this.data.length)
        {
            this.data = PApplet.subset(this.data, 0, this.count);
        }
    }

    public int size()
    {
        return this.count;
    }

    public void resize(int length)
    {
        if (length > this.data.length)
        {
            int[] temp = new int[length];
            System.arraycopy(this.data, 0, temp, 0, this.count);
            this.data = temp;
        }
        else if (length > this.count)
        {
            Arrays.fill(this.data, this.count, length, 0);
        }
        this.count = length;
    }

    public void clear()
    {
        this.count = 0;
    }

    public int get(int index)
    {
        if (index >= this.count)
        {
            throw new ArrayIndexOutOfBoundsException(index);
        }
        return this.data[index];
    }

    public void set(int index, int what)
    {
        if (index >= this.count)
        {
            this.data = PApplet.expand(this.data, index + 1);
            for (int i = this.count; i < index; ++i)
            {
                this.data[i] = 0;
            }
            this.count = index + 1;
        }
        this.data[index] = what;
    }

    public void push(int value)
    {
        this.append(value);
    }

    public int pop()
    {
        if (this.count == 0)
        {
            throw new RuntimeException("Can't call pop() on an empty list");
        }
        int value = this.get(this.count - 1);
        --this.count;
        return value;
    }

    public int remove(int index)
    {
        if (index < 0 || index >= this.count)
        {
            throw new ArrayIndexOutOfBoundsException(index);
        }
        int entry = this.data[index];
        for (int i = index; i < this.count - 1; ++i)
        {
            this.data[i] = this.data[i + 1];
        }
        --this.count;
        return entry;
    }

    public int removeValue(int value)
    {
        int index = this.index(value);
        if (index != -1)
        {
            this.remove(index);
            return index;
        }
        return -1;
    }

    public int removeValues(int value)
    {
        int ii = 0;
        for (int i = 0; i < this.count; ++i)
        {
            if (this.data[i] == value)
                continue;
            this.data[ii++] = this.data[i];
        }
        int removed = this.count - ii;
        this.count = ii;
        return removed;
    }

    public void append(int value)
    {
        if (this.count == this.data.length)
        {
            this.data = PApplet.expand(this.data);
        }
        this.data[this.count++] = value;
    }

    public void append(int[] values)
    {
        for (int v : values)
        {
            this.append(v);
        }
    }

    public void append(IntList list)
    {
        for (int v : list.values())
        {
            this.append(v);
        }
    }

    public void appendUnique(int value)
    {
        if (!this.hasValue(value))
        {
            this.append(value);
        }
    }

    public void insert(int index, int value)
    {
        this.insert(index, new int[] { value });
    }

    public void insert(int index, int[] values)
    {
        if (index < 0)
        {
            throw new IllegalArgumentException("insert() index cannot be negative: it was " + index);
        }
        if (index >= this.data.length)
        {
            throw new IllegalArgumentException("insert() index " + index + " is past the end of this list");
        }
        int[] temp = new int[this.count + values.length];
        System.arraycopy(this.data, 0, temp, 0, Math.min(this.count, index));
        System.arraycopy(values, 0, temp, index, values.length);
        System.arraycopy(this.data, index, temp, index + values.length, this.count - index);
        this.count += values.length;
        this.data = temp;
    }

    public void insert(int index, IntList list)
    {
        this.insert(index, list.values());
    }

    public int index(int what)
    {
        for (int i = 0; i < this.count; ++i)
        {
            if (this.data[i] != what)
                continue;
            return i;
        }
        return -1;
    }

    public boolean hasValue(int value)
    {
        for (int i = 0; i < this.count; ++i)
        {
            if (this.data[i] != value)
                continue;
            return true;
        }
        return false;
    }

    public void increment(int index)
    {
        if (this.count <= index)
        {
            this.resize(index + 1);
        }
        int[] arrn = this.data;
        int n = index;
        arrn[n] = arrn[n] + 1;
    }

    private void boundsProblem(int index, String method)
    {
        String msg = String.format("The list size is %d. You cannot %s() to element %d.", this.count, method, index);
        throw new ArrayIndexOutOfBoundsException(msg);
    }

    public void add(int index, int amount)
    {
        if (index < this.count)
        {
            int[] arrn = this.data;
            int n = index;
            arrn[n] = arrn[n] + amount;
        }
        else
        {
            this.boundsProblem(index, "add");
        }
    }

    public void sub(int index, int amount)
    {
        if (index < this.count)
        {
            int[] arrn = this.data;
            int n = index;
            arrn[n] = arrn[n] - amount;
        }
        else
        {
            this.boundsProblem(index, "sub");
        }
    }

    public void mult(int index, int amount)
    {
        if (index < this.count)
        {
            int[] arrn = this.data;
            int n = index;
            arrn[n] = arrn[n] * amount;
        }
        else
        {
            this.boundsProblem(index, "mult");
        }
    }

    public void div(int index, int amount)
    {
        if (index < this.count)
        {
            int[] arrn = this.data;
            int n = index;
            arrn[n] = arrn[n] / amount;
        }
        else
        {
            this.boundsProblem(index, "div");
        }
    }

    private void checkMinMax(String functionName)
    {
        if (this.count == 0)
        {
            String msg = String.format("Cannot use %s() on an empty %s.", functionName,
                                       this.getClass().getSimpleName());
            throw new RuntimeException(msg);
        }
    }

    public int min()
    {
        this.checkMinMax("min");
        int outgoing = this.data[0];
        for (int i = 1; i < this.count; ++i)
        {
            if (this.data[i] >= outgoing)
                continue;
            outgoing = this.data[i];
        }
        return outgoing;
    }

    public int minIndex()
    {
        this.checkMinMax("minIndex");
        int value = this.data[0];
        int index = 0;
        for (int i = 1; i < this.count; ++i)
        {
            if (this.data[i] >= value)
                continue;
            value = this.data[i];
            index = i;
        }
        return index;
    }

    public int max()
    {
        this.checkMinMax("max");
        int outgoing = this.data[0];
        for (int i = 1; i < this.count; ++i)
        {
            if (this.data[i] <= outgoing)
                continue;
            outgoing = this.data[i];
        }
        return outgoing;
    }

    public int maxIndex()
    {
        this.checkMinMax("maxIndex");
        int value = this.data[0];
        int index = 0;
        for (int i = 1; i < this.count; ++i)
        {
            if (this.data[i] <= value)
                continue;
            value = this.data[i];
            index = i;
        }
        return index;
    }

    public int sum()
    {
        long amount = this.sumLong();
        if (amount > Integer.MAX_VALUE)
        {
            throw new RuntimeException("sum() exceeds 2147483647, use sumLong()");
        }
        if (amount < Integer.MIN_VALUE)
        {
            throw new RuntimeException("sum() less than -2147483648, use sumLong()");
        }
        return (int) amount;
    }

    public long sumLong()
    {
        long sum = 0L;
        for (int i = 0; i < this.count; ++i)
        {
            sum += (long) this.data[i];
        }
        return sum;
    }

    public void sort()
    {
        Arrays.sort(this.data, 0, this.count);
    }

    public void sortReverse()
    {
        new Sort()
        {

            @Override
            public int size()
            {
                return IntList.this.count;
            }

            @Override
            public int compare(int a, int b)
            {
                return IntList.this.data[b] - IntList.this.data[a];
            }

            @Override
            public void swap(int a, int b)
            {
                int temp = IntList.this.data[a];
                IntList.this.data[a] = IntList.this.data[b];
                IntList.this.data[b] = temp;
            }
        } .run();
    }

    public void reverse()
    {
        int ii = this.count - 1;
        for (int i = 0; i < this.count / 2; ++i)
        {
            int t = this.data[i];
            this.data[i] = this.data[ii];
            this.data[ii] = t;
            --ii;
        }
    }

    public void shuffle()
    {
        Random r = new Random();
        int num = this.count;
        while (num > 1)
        {
            int value = r.nextInt(num);
            int temp = this.data[--num];
            this.data[num] = this.data[value];
            this.data[value] = temp;
        }
    }

    public void shuffle(PApplet sketch)
    {
        int num = this.count;
        while (num > 1)
        {
            int value = (int) sketch.random(num);
            int temp = this.data[--num];
            this.data[num] = this.data[value];
            this.data[value] = temp;
        }
    }

    public IntList copy()
    {
        IntList outgoing = new IntList(this.data);
        outgoing.count = this.count;
        return outgoing;
    }

    public int[] values()
    {
        this.crop();
        return this.data;
    }

    @Override
    public Iterator<Integer> iterator()
    {
        return new Iterator<Integer>()
        {
            int index = -1;

            @Override
            public void remove()
            {
                IntList.this.remove(this.index);
                --this.index;
            }

            @Override
            public Integer next()
            {
                return IntList.this.data[++this.index];
            }

            @Override
            public boolean hasNext()
            {
                return this.index + 1 < IntList.this.count;
            }
        };
    }

    public int[] array()
    {
        return this.array(null);
    }

    public int[] array(int[] array)
    {
        if (array == null || array.length != this.count)
        {
            array = new int[this.count];
        }
        System.arraycopy(this.data, 0, array, 0, this.count);
        return array;
    }

    public FloatList getPercent()
    {
        double sum = 0.0;
        int[] arrn = this.array();
        int n = arrn.length;
        for (int i = 0; i < n; ++i)
        {
            float value = arrn[i];
            sum += (double) value;
        }
        FloatList outgoing = new FloatList(this.count);
        for (int i = 0; i < this.count; ++i)
        {
            double percent = (double) this.data[i] / sum;
            outgoing.set(i, (float) percent);
        }
        return outgoing;
    }

    public IntList getSubset(int start)
    {
        return this.getSubset(start, this.count - start);
    }

    public IntList getSubset(int start, int num)
    {
        int[] subset = new int[num];
        System.arraycopy(this.data, start, subset, 0, num);
        return new IntList(subset);
    }

    public String join(String separator)
    {
        if (this.count == 0)
        {
            return "";
        }
        StringBuilder sb = new StringBuilder();
        sb.append(this.data[0]);
        for (int i = 1; i < this.count; ++i)
        {
            sb.append(separator);
            sb.append(this.data[i]);
        }
        return sb.toString();
    }

    public void print()
    {
        for (int i = 0; i < this.count; ++i)
        {
            System.out.format("[%d] %d%n", i, this.data[i]);
        }
    }

    public void write(PrintWriter writer)
    {
        for (int i = 0; i < this.count; ++i)
        {
            writer.println(this.data[i]);
        }
        writer.flush();
    }

    public String toJSON()
    {
        return "[ " + this.join(", ") + " ]";
    }

    public String toString()
    {
        return this.getClass().getSimpleName() + " size=" + this.size() + " " + this.toJSON();
    }

}

class JSONObject
{
    private static final int keyPoolSize = 100;
    private static HashMap<String, Object> keyPool = new HashMap(100);
    private final HashMap<String, Object> map = new HashMap();
    public static final Object NULL = new Null();

    public JSONObject()
    {
    }

    public JSONObject(Reader reader)
    {
        this(new JSONTokener(reader));
    }

    protected JSONObject(JSONTokener x)
    {
        this();
        if (x.nextClean() != '{')
        {
            throw new RuntimeException("A JSONObject text must begin with '{'");
        }
        block8: do
        {
            char c = x.nextClean();
            switch (c)
            {
            case '\u0000':
            {
                throw new RuntimeException("A JSONObject text must end with '}'");
            }
            case '}':
            {
                return;
            }
            }
            x.back();
            String key = x.nextValue().toString();
            c = x.nextClean();
            if (c == '=')
            {
                if (x.next() != '>')
                {
                    x.back();
                }
            }
            else if (c != ':')
            {
                throw new RuntimeException("Expected a ':' after a key");
            }
            this.putOnce(key, x.nextValue());
            switch (x.nextClean())
            {
            case ',':
            case ';':
            {
                if (x.nextClean() == '}')
                {
                    return;
                }
                x.back();
                continue block8;
            }
            case '}':
            {
                return;
            }
            }
            break;
        }
        while (true);
        throw new RuntimeException("Expected a ',' or '}'");
    }

    protected JSONObject(HashMap<String, Object> map)
    {
        if (map != null)
        {
            for (Map.Entry<String, Object> e : map.entrySet())
            {
                Object value = e.getValue();
                if (value == null)
                    continue;
                map.put(e.getKey(), JSONObject.wrap(value));
            }
        }
    }

    public JSONObject(IntDict dict)
    {
        for (int i = 0; i < dict.size(); ++i)
        {
            this.setInt(dict.key(i), dict.value(i));
        }
    }

    public JSONObject(FloatDict dict)
    {
        for (int i = 0; i < dict.size(); ++i)
        {
            this.setFloat(dict.key(i), dict.value(i));
        }
    }

    public JSONObject(StringDict dict)
    {
        for (int i = 0; i < dict.size(); ++i)
        {
            this.setString(dict.key(i), dict.value(i));
        }
    }

    protected JSONObject(Object bean)
    {
        this();
        this.populateMap(bean);
    }

    public static JSONObject parse(String source)
    {
        return new JSONObject(new JSONTokener(source));
    }

    protected static String doubleToString(double d)
    {
        if (Double.isInfinite(d) || Double.isNaN(d))
        {
            return "null";
        }
        String string = Double.toString(d);
        if (string.indexOf(46) > 0 && string.indexOf(101) < 0 && string.indexOf(69) < 0)
        {
            while (string.endsWith("0"))
            {
                string = string.substring(0, string.length() - 1);
            }
            if (string.endsWith("."))
            {
                string = string.substring(0, string.length() - 1);
            }
        }
        return string;
    }

    public Object get(String key)
    {
        if (key == null)
        {
            throw new RuntimeException("JSONObject.get(null) called");
        }
        Object object = this.opt(key);
        if (object == null)
        {
            return null;
        }
        if (object == null)
        {
            throw new RuntimeException("JSONObject[" + JSONObject.quote(key) + "] not found");
        }
        return object;
    }

    public String getString(String key)
    {
        Object object = this.get(key);
        if (object == null)
        {
            return null;
        }
        if (object instanceof String)
        {
            return (String) object;
        }
        throw new RuntimeException("JSONObject[" + JSONObject.quote(key) + "] is not a string");
    }

    public String getString(String key, String defaultValue)
    {
        Object object = this.opt(key);
        return NULL.equals(object) ? defaultValue : object.toString();
    }

    public int getInt(String key)
    {
        Object object = this.get(key);
        if (object == null)
        {
            throw new RuntimeException("JSONObject[" + JSONObject.quote(key) + "] not found");
        }
        try
        {
            return object instanceof Number ? ((Number) object).intValue() : Integer.parseInt((String) object);
        }
        catch (Exception e)
        {
            throw new RuntimeException("JSONObject[" + JSONObject.quote(key) + "] is not an int.");
        }
    }

    public int getInt(String key, int defaultValue)
    {
        try
        {
            return this.getInt(key);
        }
        catch (Exception e)
        {
            return defaultValue;
        }
    }

    public long getLong(String key)
    {
        Object object = this.get(key);
        try
        {
            return object instanceof Number ? ((Number) object).longValue() : Long.parseLong((String) object);
        }
        catch (Exception e)
        {
            throw new RuntimeException("JSONObject[" + JSONObject.quote(key) + "] is not a long.", e);
        }
    }

    public long getLong(String key, long defaultValue)
    {
        try
        {
            return this.getLong(key);
        }
        catch (Exception e)
        {
            return defaultValue;
        }
    }

    public float getFloat(String key)
    {
        return (float) this.getDouble(key);
    }

    public float getFloat(String key, float defaultValue)
    {
        try
        {
            return this.getFloat(key);
        }
        catch (Exception e)
        {
            return defaultValue;
        }
    }

    public double getDouble(String key)
    {
        Object object = this.get(key);
        try
        {
            return object instanceof Number ? ((Number) object).doubleValue() : Double.parseDouble((String) object);
        }
        catch (Exception e)
        {
            throw new RuntimeException("JSONObject[" + JSONObject.quote(key) + "] is not a number.");
        }
    }

    public double getDouble(String key, double defaultValue)
    {
        try
        {
            return this.getDouble(key);
        }
        catch (Exception e)
        {
            return defaultValue;
        }
    }

    public boolean getBoolean(String key)
    {
        Object object = this.get(key);
        if (object.equals(Boolean.FALSE) || object instanceof String && ((String) object).equalsIgnoreCase("false"))
        {
            return false;
        }
        if (object.equals(Boolean.TRUE) || object instanceof String && ((String) object).equalsIgnoreCase("true"))
        {
            return true;
        }
        throw new RuntimeException("JSONObject[" + JSONObject.quote(key) + "] is not a Boolean.");
    }

    public boolean getBoolean(String key, boolean defaultValue)
    {
        try
        {
            return this.getBoolean(key);
        }
        catch (Exception e)
        {
            return defaultValue;
        }
    }

    public JSONArray getJSONArray(String key)
    {
        Object object = this.get(key);
        if (object == null)
        {
            return null;
        }
        if (object instanceof JSONArray)
        {
            return (JSONArray) object;
        }
        throw new RuntimeException("JSONObject[" + JSONObject.quote(key) + "] is not a JSONArray.");
    }

    public JSONObject getJSONObject(String key)
    {
        Object object = this.get(key);
        if (object == null)
        {
            return null;
        }
        if (object instanceof JSONObject)
        {
            return (JSONObject) object;
        }
        throw new RuntimeException("JSONObject[" + JSONObject.quote(key) + "] is not a JSONObject.");
    }

    public boolean hasKey(String key)
    {
        return this.map.containsKey(key);
    }

    public boolean isNull(String key)
    {
        return NULL.equals(this.opt(key));
    }

    public Iterator keyIterator()
    {
        return this.map.keySet().iterator();
    }

    public Set keys()
    {
        return this.map.keySet();
    }

    public int size()
    {
        return this.map.size();
    }

    private static String numberToString(Number number)
    {
        if (number == null)
        {
            throw new RuntimeException("Null pointer");
        }
        JSONObject.testValidity(number);
        String string = number.toString();
        if (string.indexOf(46) > 0 && string.indexOf(101) < 0 && string.indexOf(69) < 0)
        {
            while (string.endsWith("0"))
            {
                string = string.substring(0, string.length() - 1);
            }
            if (string.endsWith("."))
            {
                string = string.substring(0, string.length() - 1);
            }
        }
        return string;
    }

    private Object opt(String key)
    {
        return key == null ? null : this.map.get(key);
    }

    private void populateMap(Object bean)
    {
        Class<?> klass = bean.getClass();
        boolean includeSuperClass = klass.getClassLoader() != null;
        Method[] methods = includeSuperClass ? klass.getMethods() : klass.getDeclaredMethods();
        for (int i = 0; i < methods.length; ++i)
        {
            try
            {
                Method method = methods[i];
                if (!Modifier.isPublic(method.getModifiers()))
                    continue;
                String name = method.getName();
                String key = "";
                if (name.startsWith("get"))
                {
                    key = "getClass".equals(name) || "getDeclaringClass".equals(name) ? "" : name.substring(3);
                }
                else if (name.startsWith("is"))
                {
                    key = name.substring(2);
                }
                if (key.length() <= 0 || !Character.isUpperCase(key.charAt(0))
                        || method.getParameterTypes().length != 0)
                    continue;
                if (key.length() == 1)
                {
                    key = key.toLowerCase();
                }
                else if (!Character.isUpperCase(key.charAt(1)))
                {
                    key = key.substring(0, 1).toLowerCase() + key.substring(1);
                }
                Object result = method.invoke(bean, (Object[])null);
                if (result == null)
                    continue;
                this.map.put(key, JSONObject.wrap(result));
                continue;
            }
            catch (Exception method)
            {
                // empty catch block
            }
        }
    }

    public JSONObject setString(String key, String value)
    {
        return this.put(key, value);
    }

    public JSONObject setInt(String key, int value)
    {
        this.put(key, value);
        return this;
    }

    public JSONObject setLong(String key, long value)
    {
        this.put(key, value);
        return this;
    }

    public JSONObject setFloat(String key, float value)
    {
        this.put(key, value);
        return this;
    }

    public JSONObject setDouble(String key, double value)
    {
        this.put(key, value);
        return this;
    }

    public JSONObject setBoolean(String key, boolean value)
    {
        this.put(key, value ? Boolean.TRUE : Boolean.FALSE);
        return this;
    }

    public JSONObject setJSONObject(String key, JSONObject value)
    {
        return this.put(key, value);
    }

    public JSONObject setJSONArray(String key, JSONArray value)
    {
        return this.put(key, value);
    }

    public JSONObject put(String key, Object value)
    {
        if (key == null)
        {
            throw new RuntimeException("Null key.");
        }
        if (value != null)
        {
            JSONObject.testValidity(value);
            String pooled = (String) keyPool.get(key);
            if (pooled == null)
            {
                if (keyPool.size() >= 100)
                {
                    keyPool = new HashMap(100);
                }
                keyPool.put(key, key);
            }
            else
            {
                key = pooled;
            }
            this.map.put(key, value);
        }
        else
        {
            this.remove(key);
        }
        return this;
    }

    private JSONObject putOnce(String key, Object value)
    {
        if (key != null && value != null)
        {
            if (this.opt(key) != null)
            {
                throw new RuntimeException("Duplicate key \"" + key + "\"");
            }
            this.put(key, value);
        }
        return this;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static String quote(String string)
    {
        StringWriter sw = new StringWriter();
        StringBuffer stringBuffer = sw.getBuffer();
        synchronized (stringBuffer)
        {
            try
            {
                return JSONObject.quote(string, sw).toString();
            }
            catch (IOException ignored)
            {
                return "";
            }
        }
    }

    public static Writer quote(String string, Writer w) throws IOException
    {
        if (string == null || string.length() == 0)
        {
            w.write("\"\"");
            return w;
        }
        char c = '\u0000';
        int len = string.length();
        w.write(34);
        block9: for (int i = 0; i < len; ++i)
        {
            char b = c;
            c = string.charAt(i);
            switch (c)
            {
            case '\"':
            case '\\':
            {
                w.write(92);
                w.write(c);
                continue block9;
            }
            case '/':
            {
                if (b == '<')
                {
                    w.write(92);
                }
                w.write(c);
                continue block9;
            }
            case '\b':
            {
                w.write("\\b");
                continue block9;
            }
            case '\t':
            {
                w.write("\\t");
                continue block9;
            }
            case '\n':
            {
                w.write("\\n");
                continue block9;
            }
            case '\f':
            {
                w.write("\\f");
                continue block9;
            }
            case '\r':
            {
                w.write("\\r");
                continue block9;
            }
            default:
            {
                throw new IOException();
            }
            }
        }
        w.write(34);
        return w;
    }

    public Object remove(String key)
    {
        return this.map.remove(key);
    }

    protected static Object stringToValue(String string)
    {
        block10:
        {
            if (string.equals(""))
            {
                return string;
            }
            if (string.equalsIgnoreCase("true"))
            {
                return Boolean.TRUE;
            }
            if (string.equalsIgnoreCase("false"))
            {
                return Boolean.FALSE;
            }
            if (string.equalsIgnoreCase("null"))
            {
                return NULL;
            }
            char b = string.charAt(0);
            if (b >= '0' && b <= '9' || b == '.' || b == '-' || b == '+')
            {
                try
                {
                    if (string.indexOf(46) > -1 || string.indexOf(101) > -1 || string.indexOf(69) > -1)
                    {
                        Double d = Double.valueOf(string);
                        if (!d.isInfinite() && !d.isNaN())
                        {
                            return d;
                        }
                        break block10;
                    }
                    Long myLong = Long.valueOf(string);
                    if (myLong == (long) myLong.intValue())
                    {
                        return myLong.intValue();
                    }
                    return myLong;
                }
                catch (Exception myLong)
                {
                    // empty catch block
                }
            }
        }
        return string;
    }

    protected static void testValidity(Object o)
    {
        if (o != null && (o instanceof Double ? ((Double) o).isInfinite() || ((Double) o).isNaN()
                          : o instanceof Float && (((Float) o).isInfinite() || ((Float) o).isNaN())))
        {
            throw new RuntimeException("JSON does not allow non-finite numbers.");
        }
    }

    public boolean write(PrintWriter output)
    {
        return this.write(output, null);
    }

    public boolean write(PrintWriter output, String options)
    {
        int indentFactor = 2;
        if (options != null)
        {
            String[] opts;
            for (String opt : opts = PApplet.split(options, ','))
            {
                if (opt.equals("compact"))
                {
                    indentFactor = -1;
                    continue;
                }
                if (opt.startsWith("indent="))
                {
                    indentFactor = PApplet.parseInt(opt.substring(7), -2);
                    if (indentFactor != -2)
                        continue;
                    throw new IllegalArgumentException("Could not read a number from " + opt);
                }
                System.err.println("Ignoring " + opt);
            }
        }
        output.print(this.format(indentFactor));
        output.flush();
        return true;
    }

    public String toString()
    {
        try
        {
            return this.format(2);
        }
        catch (Exception e)
        {
            return null;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public String format(int indentFactor)
    {
        StringWriter w = new StringWriter();
        StringBuffer stringBuffer = w.getBuffer();
        synchronized (stringBuffer)
        {
            return this.writeInternal(w, indentFactor, 0).toString();
        }
    }

    protected static String valueToString(Object value)
    {
        if (value == null || value.equals(null))
        {
            return "null";
        }
        if (value instanceof Number)
        {
            return JSONObject.numberToString((Number) value);
        }
        if (value instanceof Boolean || value instanceof JSONObject || value instanceof JSONArray)
        {
            return value.toString();
        }
        if (value instanceof Map)
        {
            return new JSONObject(value).toString();
        }
        if (value instanceof Collection)
        {
            return new JSONArray(value).toString();
        }
        if (value.getClass().isArray())
        {
            return new JSONArray(value).toString();
        }
        return JSONObject.quote(value.toString());
    }

    protected static Object wrap(Object object)
    {
        try
        {
            String objectPackageName;
            if (object == null)
            {
                return NULL;
            }
            if (object instanceof JSONObject || object instanceof JSONArray || NULL.equals(object)
                    || object instanceof Byte || object instanceof Character || object instanceof Short
                    || object instanceof Integer || object instanceof Long || object instanceof Boolean
                    || object instanceof Float || object instanceof Double || object instanceof String)
            {
                return object;
            }
            if (object instanceof Collection)
            {
                return new JSONArray(object);
            }
            if (object.getClass().isArray())
            {
                return new JSONArray(object);
            }
            if (object instanceof Map)
            {
                return new JSONObject(object);
            }
            Package objectPackage = object.getClass().getPackage();
            String string = objectPackageName = objectPackage != null ? objectPackage.getName() : "";
            if (objectPackageName.startsWith("java.") || objectPackageName.startsWith("javax.")
                    || object.getClass().getClassLoader() == null)
            {
                return object.toString();
            }
            return new JSONObject(object);
        }
        catch (Exception exception)
        {
            return null;
        }
    }

    static final Writer writeValue(Writer writer, Object value, int indentFactor, int indent) throws IOException
    {
        if (value == null || value.equals(null))
        {
            writer.write("null");
        }
        else if (value instanceof JSONObject)
        {
            ((JSONObject) value).writeInternal(writer, indentFactor, indent);
        }
        else if (value instanceof JSONArray)
        {
            ((JSONArray) value).writeInternal(writer, indentFactor, indent);
        }
        else if (value instanceof Map)
        {
            new JSONObject(value).writeInternal(writer, indentFactor, indent);
        }
        else if (value instanceof Collection)
        {
            new JSONArray(value).writeInternal(writer, indentFactor, indent);
        }
        else if (value.getClass().isArray())
        {
            new JSONArray(value).writeInternal(writer, indentFactor, indent);
        }
        else if (value instanceof Number)
        {
            writer.write(JSONObject.numberToString((Number) value));
        }
        else if (value instanceof Boolean)
        {
            writer.write(value.toString());
        }
        else
        {
            JSONObject.quote(value.toString(), writer);
        }
        return writer;
    }

    static final void indent(Writer writer, int indent) throws IOException
    {
        for (int i = 0; i < indent; ++i)
        {
            writer.write(32);
        }
    }

    protected Writer writeInternal(Writer writer, int indentFactor, int indent)
    {
        try
        {
            int actualFactor;
            boolean commanate = false;
            int length = this.size();
            Iterator keys = this.keyIterator();
            writer.write(123);
            int n = actualFactor = indentFactor == -1 ? 0 : indentFactor;
            if (length == 1)
            {
                Object key = keys.next();
                writer.write(JSONObject.quote(key.toString()));
                writer.write(58);
                if (actualFactor > 0)
                {
                    writer.write(32);
                }
                JSONObject.writeValue(writer, this.map.get(key), indentFactor, indent);
            }
            else if (length != 0)
            {
                int newIndent = indent + actualFactor;
                while (keys.hasNext())
                {
                    Object key = keys.next();
                    if (commanate)
                    {
                        writer.write(44);
                    }
                    if (indentFactor != -1)
                    {
                        writer.write(10);
                    }
                    JSONObject.indent(writer, newIndent);
                    writer.write(JSONObject.quote(key.toString()));
                    writer.write(58);
                    if (actualFactor > 0)
                    {
                        writer.write(32);
                    }
                    JSONObject.writeValue(writer, this.map.get(key), indentFactor, newIndent);
                    commanate = true;
                }
                if (indentFactor != -1)
                {
                    writer.write(10);
                }
                JSONObject.indent(writer, indent);
            }
            writer.write(125);
            return writer;
        }
        catch (IOException exception)
        {
            throw new RuntimeException(exception);
        }
    }

    private static final class Null
    {
        private Null()
        {
        }

        protected final Object clone()
        {
            return this;
        }

        public boolean equals(Object object)
        {
            return object == null || object == this;
        }

        public String toString()
        {
            return "null";
        }

        public int hashCode()
        {
            return super.hashCode();
        }
    }

}

class JSONTokener
{
    private long character;
    private boolean eof;
    private long index;
    private long line;
    private char previous;
    private Reader reader;
    private boolean usePrevious;

    public JSONTokener(Reader reader)
    {
        this.reader = reader.markSupported() ? reader : new BufferedReader(reader);
        this.eof = false;
        this.usePrevious = false;
        this.previous = '\u0000';
        this.index = 0L;
        this.character = 1L;
        this.line = 1L;
    }

    public JSONTokener(InputStream inputStream)
    {
        this(new InputStreamReader(inputStream));
    }

    public JSONTokener(String s)
    {
        this(new StringReader(s));
    }

    public void back()
    {
        if (this.usePrevious || this.index <= 0L)
        {
            throw new RuntimeException("Stepping back two steps is not supported");
        }
        --this.index;
        --this.character;
        this.usePrevious = true;
        this.eof = false;
    }

    public static int dehexchar(char c)
    {
        if (c >= '0' && c <= '9')
        {
            return c - 48;
        }
        if (c >= 'A' && c <= 'F')
        {
            return c - 55;
        }
        if (c >= 'a' && c <= 'f')
        {
            return c - 87;
        }
        return -1;
    }

    public boolean end()
    {
        return this.eof && !this.usePrevious;
    }

    public boolean more()
    {
        this.next();
        if (this.end())
        {
            return false;
        }
        this.back();
        return true;
    }

    public char next()
    {
        int c;
        if (this.usePrevious)
        {
            this.usePrevious = false;
            c = this.previous;
        }
        else
        {
            try
            {
                c = this.reader.read();
            }
            catch (IOException exception)
            {
                throw new RuntimeException(exception);
            }
            if (c <= 0)
            {
                this.eof = true;
                c = 0;
            }
        }
        ++this.index;
        if (this.previous == '\r')
        {
            ++this.line;
            this.character = c == 10 ? 0L : 1L;
        }
        else if (c == 10)
        {
            ++this.line;
            this.character = 0L;
        }
        else
        {
            ++this.character;
        }
        this.previous = (char) c;
        return this.previous;
    }

    public char next(char c)
    {
        char n = this.next();
        if (n != c)
        {
            throw new RuntimeException("Expected '" + c + "' and instead saw '" + n + "'");
        }
        return n;
    }

    public String next(int n)
    {
        if (n == 0)
        {
            return "";
        }
        char[] chars = new char[n];
        for (int pos = 0; pos < n; ++pos)
        {
            chars[pos] = this.next();
            if (!this.end())
                continue;
            throw new RuntimeException("Substring bounds error");
        }
        return new String(chars);
    }

    public char nextClean()
    {
        char c;
        while ((c = this.next()) != '\u0000' && c <= ' ')
        {
        }
        return c;
    }

    public String nextString(char quote)
    {
        StringBuilder sb = new StringBuilder();
        block13: do
        {
            char c = this.next();
            switch (c)
            {
            case '\u0000':
            case '\n':
            case '\r':
            {
                throw new RuntimeException("Unterminated string");
            }
            case '\\':
            {
                c = this.next();
                switch (c)
                {
                case 'b':
                {
                    sb.append('\b');
                    continue block13;
                }
                case 't':
                {
                    sb.append('\t');
                    continue block13;
                }
                case 'n':
                {
                    sb.append('\n');
                    continue block13;
                }
                case 'f':
                {
                    sb.append('\f');
                    continue block13;
                }
                case 'r':
                {
                    sb.append('\r');
                    continue block13;
                }
                case 'u':
                {
                    sb.append((char) Integer.parseInt(this.next(4), 16));
                    continue block13;
                }
                case '\"':
                case '\'':
                case '/':
                case '\\':
                {
                    sb.append(c);
                    continue block13;
                }
                }
                throw new RuntimeException("Illegal escape.");
            }
            }
            if (c == quote)
            {
                return sb.toString();
            }
            sb.append(c);
        }
        while (true);
    }

    public String nextTo(char delimiter)
    {
        StringBuilder sb = new StringBuilder();
        do
        {
            char c;
            if ((c = this.next()) == delimiter || c == '\u0000' || c == '\n' || c == '\r')
            {
                if (c != '\u0000')
                {
                    this.back();
                }
                return sb.toString().trim();
            }
            sb.append(c);
        }
        while (true);
    }

    public String nextTo(String delimiters)
    {
        StringBuilder sb = new StringBuilder();
        do
        {
            char c;
            if (delimiters.indexOf(c = this.next()) >= 0 || c == '\u0000' || c == '\n' || c == '\r')
            {
                if (c != '\u0000')
                {
                    this.back();
                }
                return sb.toString().trim();
            }
            sb.append(c);
        }
        while (true);
    }

    public Object nextValue()
    {
        char c = this.nextClean();
        switch (c)
        {
        case '\"':
        case '\'':
        {
            return this.nextString(c);
        }
        case '{':
        {
            this.back();
            return new JSONObject(this);
        }
        case '[':
        {
            this.back();
            return new JSONArray(this);
        }
        }
        StringBuilder sb = new StringBuilder();
        while (c >= ' ' && ",:]}/\\\"[{;=#".indexOf(c) < 0)
        {
            sb.append(c);
            c = this.next();
        }
        this.back();
        String string = sb.toString().trim();
        if ("".equals(string))
        {
            throw new RuntimeException("Missing value");
        }
        return JSONObject.stringToValue(string);
    }

    public char skipTo(char to)
    {
        char c;
        try
        {
            long startIndex = this.index;
            long startCharacter = this.character;
            long startLine = this.line;
            this.reader.mark(1000000);
            do
            {
                if ((c = this.next()) != '\u0000')
                    continue;
                this.reader.reset();
                this.index = startIndex;
                this.character = startCharacter;
                this.line = startLine;
                return c;
            }
            while (c != to);
        }
        catch (IOException exc)
        {
            throw new RuntimeException(exc);
        }
        this.back();
        return c;
    }

    public String toString()
    {
        return " at " + this.index + " [character " + this.character + " line " + this.line + "]";
    }
}

class JSONArray
{
    private final ArrayList<Object> myArrayList = new ArrayList();

    public JSONArray()
    {
    }

    public JSONArray(Reader reader)
    {
        this(new JSONTokener(reader));
    }

    protected JSONArray(JSONTokener x)
    {
        this();
        if (x.nextClean() != '[')
        {
            throw new RuntimeException("A JSONArray text must start with '['");
        }
        if (x.nextClean() != ']')
        {
            x.back();
            block4: do
            {
                if (x.nextClean() == ',')
                {
                    x.back();
                    this.myArrayList.add(JSONObject.NULL);
                }
                else
                {
                    x.back();
                    this.myArrayList.add(x.nextValue());
                }
                switch (x.nextClean())
                {
                case ',':
                case ';':
                {
                    if (x.nextClean() == ']')
                    {
                        return;
                    }
                    x.back();
                    continue block4;
                }
                case ']':
                {
                    return;
                }
                }
                break;
            }
            while (true);
            throw new RuntimeException("Expected a ',' or ']'");
        }
    }

    public JSONArray(IntList list)
    {
        for (int item : list.values())
        {
            this.myArrayList.add(item);
        }
    }

    public JSONArray(FloatList list)
    {
        for (float item : list.values())
        {
            this.myArrayList.add(Float.valueOf(item));
        }
    }

    public JSONArray(StringList list)
    {
        for (String item : list.values())
        {
            this.myArrayList.add(item);
        }
    }

    public static JSONArray parse(String source)
    {
        try
        {
            return new JSONArray(new JSONTokener(source));
        }
        catch (Exception e)
        {
            return null;
        }
    }

    protected JSONArray(Object array)
    {
        this();
        if (array.getClass().isArray())
        {
            int length = Array.getLength(array);
            for (int i = 0; i < length; ++i)
            {
                this.append(JSONObject.wrap(Array.get(array, i)));
            }
        }
        else
        {
            throw new RuntimeException("JSONArray initial value should be a string or collection or array.");
        }
    }

    private Object opt(int index)
    {
        if (index < 0 || index >= this.size())
        {
            return null;
        }
        return this.myArrayList.get(index);
    }

    public Object get(int index)
    {
        Object object = this.opt(index);
        if (object == null)
        {
            throw new RuntimeException("JSONArray[" + index + "] not found.");
        }
        return object;
    }

    public String getString(int index)
    {
        Object object = this.get(index);
        if (object instanceof String)
        {
            return (String) object;
        }
        throw new RuntimeException("JSONArray[" + index + "] not a string.");
    }

    public String getString(int index, String defaultValue)
    {
        Object object = this.opt(index);
        return JSONObject.NULL.equals(object) ? defaultValue : object.toString();
    }

    public int getInt(int index)
    {
        Object object = this.get(index);
        try
        {
            return object instanceof Number ? ((Number) object).intValue() : Integer.parseInt((String) object);
        }
        catch (Exception e)
        {
            throw new RuntimeException("JSONArray[" + index + "] is not a number.");
        }
    }

    public int getInt(int index, int defaultValue)
    {
        try
        {
            return this.getInt(index);
        }
        catch (Exception e)
        {
            return defaultValue;
        }
    }

    public long getLong(int index)
    {
        Object object = this.get(index);
        try
        {
            return object instanceof Number ? ((Number) object).longValue() : Long.parseLong((String) object);
        }
        catch (Exception e)
        {
            throw new RuntimeException("JSONArray[" + index + "] is not a number.");
        }
    }

    public long getLong(int index, long defaultValue)
    {
        try
        {
            return this.getLong(index);
        }
        catch (Exception e)
        {
            return defaultValue;
        }
    }

    public float getFloat(int index)
    {
        return (float) this.getDouble(index);
    }

    public float getFloat(int index, float defaultValue)
    {
        try
        {
            return this.getFloat(index);
        }
        catch (Exception e)
        {
            return defaultValue;
        }
    }

    public double getDouble(int index)
    {
        Object object = this.get(index);
        try
        {
            return object instanceof Number ? ((Number) object).doubleValue() : Double.parseDouble((String) object);
        }
        catch (Exception e)
        {
            throw new RuntimeException("JSONArray[" + index + "] is not a number.");
        }
    }

    public double getDouble(int index, double defaultValue)
    {
        try
        {
            return this.getDouble(index);
        }
        catch (Exception e)
        {
            return defaultValue;
        }
    }

    public boolean getBoolean(int index)
    {
        Object object = this.get(index);
        if (object.equals(Boolean.FALSE) || object instanceof String && ((String) object).equalsIgnoreCase("false"))
        {
            return false;
        }
        if (object.equals(Boolean.TRUE) || object instanceof String && ((String) object).equalsIgnoreCase("true"))
        {
            return true;
        }
        throw new RuntimeException("JSONArray[" + index + "] is not a boolean.");
    }

    public boolean getBoolean(int index, boolean defaultValue)
    {
        try
        {
            return this.getBoolean(index);
        }
        catch (Exception e)
        {
            return defaultValue;
        }
    }

    public JSONArray getJSONArray(int index)
    {
        Object object = this.get(index);
        if (object instanceof JSONArray)
        {
            return (JSONArray) object;
        }
        throw new RuntimeException("JSONArray[" + index + "] is not a JSONArray.");
    }

    public JSONArray getJSONArray(int index, JSONArray defaultValue)
    {
        try
        {
            return this.getJSONArray(index);
        }
        catch (Exception e)
        {
            return defaultValue;
        }
    }

    public JSONObject getJSONObject(int index)
    {
        Object object = this.get(index);
        if (object instanceof JSONObject)
        {
            return (JSONObject) object;
        }
        throw new RuntimeException("JSONArray[" + index + "] is not a JSONObject.");
    }

    public JSONObject getJSONObject(int index, JSONObject defaultValue)
    {
        try
        {
            return this.getJSONObject(index);
        }
        catch (Exception e)
        {
            return defaultValue;
        }
    }

    public String[] getStringArray()
    {
        String[] outgoing = new String[this.size()];
        for (int i = 0; i < this.size(); ++i)
        {
            outgoing[i] = this.getString(i);
        }
        return outgoing;
    }

    public int[] getIntArray()
    {
        int[] outgoing = new int[this.size()];
        for (int i = 0; i < this.size(); ++i)
        {
            outgoing[i] = this.getInt(i);
        }
        return outgoing;
    }

    public long[] getLongArray()
    {
        long[] outgoing = new long[this.size()];
        for (int i = 0; i < this.size(); ++i)
        {
            outgoing[i] = this.getLong(i);
        }
        return outgoing;
    }

    public float[] getFloatArray()
    {
        float[] outgoing = new float[this.size()];
        for (int i = 0; i < this.size(); ++i)
        {
            outgoing[i] = this.getFloat(i);
        }
        return outgoing;
    }

    public double[] getDoubleArray()
    {
        double[] outgoing = new double[this.size()];
        for (int i = 0; i < this.size(); ++i)
        {
            outgoing[i] = this.getDouble(i);
        }
        return outgoing;
    }

    public boolean[] getBooleanArray()
    {
        boolean[] outgoing = new boolean[this.size()];
        for (int i = 0; i < this.size(); ++i)
        {
            outgoing[i] = this.getBoolean(i);
        }
        return outgoing;
    }

    public JSONArray append(String value)
    {
        this.append((Object) value);
        return this;
    }

    public JSONArray append(int value)
    {
        this.append((Object) value);
        return this;
    }

    public JSONArray append(long value)
    {
        this.append((Object) value);
        return this;
    }

    public JSONArray append(float value)
    {
        return this.append((double) value);
    }

    public JSONArray append(double value)
    {
        Double d = value;
        JSONObject.testValidity(d);
        this.append(d);
        return this;
    }

    public JSONArray append(boolean value)
    {
        this.append(value ? Boolean.TRUE : Boolean.FALSE);
        return this;
    }

    public JSONArray append(JSONArray value)
    {
        this.myArrayList.add(value);
        return this;
    }

    public JSONArray append(JSONObject value)
    {
        this.myArrayList.add(value);
        return this;
    }

    protected JSONArray append(Object value)
    {
        this.myArrayList.add(value);
        return this;
    }

    public JSONArray setString(int index, String value)
    {
        this.set(index, value);
        return this;
    }

    public JSONArray setInt(int index, int value)
    {
        this.set(index, value);
        return this;
    }

    public JSONArray setLong(int index, long value)
    {
        return this.set(index, value);
    }

    public JSONArray setFloat(int index, float value)
    {
        return this.setDouble(index, value);
    }

    public JSONArray setDouble(int index, double value)
    {
        return this.set(index, value);
    }

    public JSONArray setBoolean(int index, boolean value)
    {
        return this.set(index, value ? Boolean.TRUE : Boolean.FALSE);
    }

    public JSONArray setJSONArray(int index, JSONArray value)
    {
        this.set(index, value);
        return this;
    }

    public JSONArray setJSONObject(int index, JSONObject value)
    {
        this.set(index, value);
        return this;
    }

    private JSONArray set(int index, Object value)
    {
        JSONObject.testValidity(value);
        if (index < 0)
        {
            throw new RuntimeException("JSONArray[" + index + "] not found.");
        }
        if (index < this.size())
        {
            this.myArrayList.set(index, value);
        }
        else
        {
            while (index != this.size())
            {
                this.append(JSONObject.NULL);
            }
            this.append(value);
        }
        return this;
    }

    public int size()
    {
        return this.myArrayList.size();
    }

    public boolean isNull(int index)
    {
        return JSONObject.NULL.equals(this.opt(index));
    }

    public Object remove(int index)
    {
        Object o = this.opt(index);
        this.myArrayList.remove(index);
        return o;
    }

    public boolean write(PrintWriter output)
    {
        return this.write(output, null);
    }

    public boolean write(PrintWriter output, String options)
    {
        int indentFactor = 2;
        if (options != null)
        {
            String[] opts;
            for (String opt : opts = PApplet.split(options, ','))
            {
                if (opt.equals("compact"))
                {
                    indentFactor = -1;
                    continue;
                }
                if (opt.startsWith("indent="))
                {
                    indentFactor = PApplet.parseInt(opt.substring(7), -2);
                    if (indentFactor != -2)
                        continue;
                    throw new IllegalArgumentException("Could not read a number from " + opt);
                }
                System.err.println("Ignoring " + opt);
            }
        }
        output.print(this.format(indentFactor));
        output.flush();
        return true;
    }

    public String toString()
    {
        try
        {
            return this.format(2);
        }
        catch (Exception e)
        {
            return null;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public String format(int indentFactor)
    {
        StringWriter sw = new StringWriter();
        StringBuffer stringBuffer = sw.getBuffer();
        synchronized (stringBuffer)
        {
            return this.writeInternal(sw, indentFactor, 0).toString();
        }
    }

    protected Writer writeInternal(Writer writer, int indentFactor, int indent)
    {
        try
        {
            int thisFactor;
            boolean commanate = false;
            int length = this.size();
            writer.write(91);
            int n = thisFactor = indentFactor == -1 ? 0 : indentFactor;
            if (length == 1)
            {
                JSONObject.writeValue(writer, this.myArrayList.get(0), indentFactor, indent);
            }
            else if (length != 0)
            {
                int newIndent = indent + thisFactor;
                for (int i = 0; i < length; ++i)
                {
                    if (commanate)
                    {
                        writer.write(44);
                    }
                    if (indentFactor != -1)
                    {
                        writer.write(10);
                    }
                    JSONObject.indent(writer, newIndent);
                    JSONObject.writeValue(writer, this.myArrayList.get(i), indentFactor, newIndent);
                    commanate = true;
                }
                if (indentFactor != -1)
                {
                    writer.write(10);
                }
                JSONObject.indent(writer, indent);
            }
            writer.write(93);
            return writer;
        }
        catch (IOException e)
        {
            throw new RuntimeException(e);
        }
    }

    public String join(String separator)
    {
        int len = this.size();
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < len; ++i)
        {
            if (i > 0)
            {
                sb.append(separator);
            }
            sb.append(JSONObject.valueToString(this.myArrayList.get(i)));
        }
        return sb.toString();
    }
}

class StringDict
{
    protected int count;
    protected String[] keys;
    protected String[] values;
    private HashMap<String, Integer> indices = new HashMap();

    public StringDict()
    {
        this.count = 0;
        this.keys = new String[10];
        this.values = new String[10];
    }

    public StringDict(int length)
    {
        this.count = 0;
        this.keys = new String[length];
        this.values = new String[length];
    }

    public StringDict(String[] keys, String[] values)
    {
        if (keys.length != values.length)
        {
            throw new IllegalArgumentException("key and value arrays must be the same length");
        }
        this.keys = keys;
        this.values = values;
        this.count = keys.length;
        for (int i = 0; i < this.count; ++i)
        {
            this.indices.put(keys[i], i);
        }
    }

    public StringDict(String[][] pairs)
    {
        this.count = pairs.length;
        this.keys = new String[this.count];
        this.values = new String[this.count];
        for (int i = 0; i < this.count; ++i)
        {
            this.keys[i] = pairs[i][0];
            this.values[i] = pairs[i][1];
            this.indices.put(this.keys[i], i);
        }
    }

    public StringDict(TableRow row)
    {
        this(row.getColumnCount());
        String[] titles = row.getColumnTitles();
        if (titles == null)
        {
            titles = new StringList(new Object[] { IntList.fromRange(row.getColumnCount()) }).array();
        }
        for (int col = 0; col < row.getColumnCount(); ++col)
        {
            this.set(titles[col], row.getString(col));
        }
        this.crop();
    }

    public int size()
    {
        return this.count;
    }

    public void resize(int length)
    {
        if (length > this.count)
        {
            throw new IllegalArgumentException("resize() can only be used to shrink the dictionary");
        }
        if (length < 1)
        {
            throw new IllegalArgumentException("resize(" + length + ") is too small, use 1 or higher");
        }
        String[] newKeys = new String[length];
        String[] newValues = new String[length];
        PApplet.arrayCopy(this.keys, newKeys, length);
        PApplet.arrayCopy(this.values, newValues, length);
        this.keys = newKeys;
        this.values = newValues;
        this.count = length;
        this.resetIndices();
    }

    public void clear()
    {
        this.count = 0;
        this.indices = new HashMap();
    }

    private void resetIndices()
    {
        this.indices = new HashMap(this.count);
        for (int i = 0; i < this.count; ++i)
        {
            this.indices.put(this.keys[i], i);
        }
    }

    public Iterable<Entry> entries()
    {
        return new Iterable<Entry>()
        {

            @Override
            public Iterator<Entry> iterator()
            {
                return StringDict.this.entryIterator();
            }
        };
    }

    public Iterator<Entry> entryIterator()
    {
        return new Iterator<Entry>()
        {
            int index = -1;

            @Override
            public void remove()
            {
                StringDict.this.removeIndex(this.index);
                --this.index;
            }

            @Override
            public Entry next()
            {
                ++this.index;
                Entry e = new Entry(StringDict.this.keys[this.index], StringDict.this.values[this.index]);
                return e;
            }

            @Override
            public boolean hasNext()
            {
                return this.index + 1 < StringDict.this.size();
            }
        };
    }

    public String key(int index)
    {
        return this.keys[index];
    }

    protected void crop()
    {
        if (this.count != this.keys.length)
        {
            this.keys = PApplet.subset(this.keys, 0, this.count);
            this.values = PApplet.subset(this.values, 0, this.count);
        }
    }

    public Iterable<String> keys()
    {
        return new Iterable<String>()
        {

            @Override
            public Iterator<String> iterator()
            {
                return StringDict.this.keyIterator();
            }
        };
    }

    public Iterator<String> keyIterator()
    {
        return new Iterator<String>()
        {
            int index = -1;

            @Override
            public void remove()
            {
                StringDict.this.removeIndex(this.index);
                --this.index;
            }

            @Override
            public String next()
            {
                return StringDict.this.key(++this.index);
            }

            @Override
            public boolean hasNext()
            {
                return this.index + 1 < StringDict.this.size();
            }
        };
    }

    public String[] keyArray()
    {
        this.crop();
        return this.keyArray(null);
    }

    public String[] keyArray(String[] outgoing)
    {
        if (outgoing == null || outgoing.length != this.count)
        {
            outgoing = new String[this.count];
        }
        System.arraycopy(this.keys, 0, outgoing, 0, this.count);
        return outgoing;
    }

    public String value(int index)
    {
        return this.values[index];
    }

    public Iterable<String> values()
    {
        return new Iterable<String>()
        {

            @Override
            public Iterator<String> iterator()
            {
                return StringDict.this.valueIterator();
            }
        };
    }

    public Iterator<String> valueIterator()
    {
        return new Iterator<String>()
        {
            int index = -1;

            @Override
            public void remove()
            {
                StringDict.this.removeIndex(this.index);
                --this.index;
            }

            @Override
            public String next()
            {
                return StringDict.this.value(++this.index);
            }

            @Override
            public boolean hasNext()
            {
                return this.index + 1 < StringDict.this.size();
            }
        };
    }

    public String[] valueArray()
    {
        this.crop();
        return this.valueArray(null);
    }

    public String[] valueArray(String[] array)
    {
        if (array == null || array.length != this.size())
        {
            array = new String[this.count];
        }
        System.arraycopy(this.values, 0, array, 0, this.count);
        return array;
    }

    public String get(String key)
    {
        int index = this.index(key);
        if (index == -1)
        {
            return null;
        }
        return this.values[index];
    }

    public String get(String key, String alternate)
    {
        int index = this.index(key);
        if (index == -1)
        {
            return alternate;
        }
        return this.values[index];
    }

    public void set(String key, String value)
    {
        int index = this.index(key);
        if (index == -1)
        {
            this.create(key, value);
        }
        else
        {
            this.values[index] = value;
        }
    }

    public void setIndex(int index, String key, String value)
    {
        if (index < 0 || index >= this.count)
        {
            throw new ArrayIndexOutOfBoundsException(index);
        }
        this.keys[index] = key;
        this.values[index] = value;
    }

    public int index(String what)
    {
        Integer found = this.indices.get(what);
        return found == null ? -1 : found;
    }

    public boolean hasKey(String key)
    {
        return this.index(key) != -1;
    }

    protected void create(String key, String value)
    {
        if (this.count == this.keys.length)
        {
            this.keys = PApplet.expand(this.keys);
            this.values = PApplet.expand(this.values);
        }
        this.indices.put(key, this.count);
        this.keys[this.count] = key;
        this.values[this.count] = value;
        ++this.count;
    }

    public String remove(String key)
    {
        int index = this.index(key);
        if (index == -1)
        {
            throw new NoSuchElementException("'" + key + "' not found");
        }
        String value = this.values[index];
        this.removeIndex(index);
        return value;
    }

    public String removeIndex(int index)
    {
        if (index < 0 || index >= this.count)
        {
            throw new ArrayIndexOutOfBoundsException(index);
        }
        String value = this.values[index];
        this.indices.remove(this.keys[index]);
        for (int i = index; i < this.count - 1; ++i)
        {
            this.keys[i] = this.keys[i + 1];
            this.values[i] = this.values[i + 1];
            this.indices.put(this.keys[i], i);
        }
        --this.count;
        this.keys[this.count] = null;
        this.values[this.count] = null;
        return value;
    }

    public void swap(int a, int b)
    {
        String tkey = this.keys[a];
        String tvalue = this.values[a];
        this.keys[a] = this.keys[b];
        this.values[a] = this.values[b];
        this.keys[b] = tkey;
        this.values[b] = tvalue;
    }

    public void sortKeys()
    {
        this.sortImpl(true, false);
    }

    public void sortKeysReverse()
    {
        this.sortImpl(true, true);
    }

    public void sortValues()
    {
        this.sortImpl(false, false);
    }

    public void sortValuesReverse()
    {
        this.sortImpl(false, true);
    }

    protected void sortImpl(final boolean useKeys, final boolean reverse)
    {
        Sort s = new Sort()
        {

            @Override
            public int size()
            {
                return StringDict.this.count;
            }

            @Override
            public int compare(int a, int b)
            {
                int diff = 0;
                if (useKeys)
                {
                    diff = StringDict.this.keys[a].compareToIgnoreCase(StringDict.this.keys[b]);
                    if (diff == 0)
                    {
                        diff = StringDict.this.values[a].compareToIgnoreCase(StringDict.this.values[b]);
                    }
                }
                else
                {
                    diff = StringDict.this.values[a].compareToIgnoreCase(StringDict.this.values[b]);
                    if (diff == 0)
                    {
                        diff = StringDict.this.keys[a].compareToIgnoreCase(StringDict.this.keys[b]);
                    }
                }
                return reverse ? -diff : diff;
            }

            @Override
            public void swap(int a, int b)
            {
                StringDict.this.swap(a, b);
            }
        };
        s.run();
        this.resetIndices();
    }

    public StringDict copy()
    {
        StringDict outgoing = new StringDict(this.count);
        System.arraycopy(this.keys, 0, outgoing.keys, 0, this.count);
        System.arraycopy(this.values, 0, outgoing.values, 0, this.count);
        for (int i = 0; i < this.count; ++i)
        {
            outgoing.indices.put(this.keys[i], i);
        }
        outgoing.count = this.count;
        return outgoing;
    }

    public void print()
    {
        for (int i = 0; i < this.size(); ++i)
        {
            System.out.println(this.keys[i] + " = " + this.values[i]);
        }
    }

    public void write(PrintWriter writer)
    {
        for (int i = 0; i < this.count; ++i)
        {
            writer.println(this.keys[i] + "\t" + this.values[i]);
        }
        writer.flush();
    }

    public String toJSON()
    {
        StringList items = new StringList();
        for (int i = 0; i < this.count; ++i)
        {
            items.append(JSONObject.quote(this.keys[i]) + ": " + JSONObject.quote(this.values[i]));
        }
        return "{ " + items.join(", ") + " }";
    }

    public String toString()
    {
        return this.getClass().getSimpleName() + " size=" + this.size() + " " + this.toJSON();
    }

    public class Entry
    {
        public String key;
        public String value;

        Entry(String key, String value)
        {
            this.key = key;
            this.value = value;
        }
    }

}

interface TableRow
{
    public String getString(int var1);

    public String getString(String var1);

    public int getInt(int var1);

    public int getInt(String var1);

    public long getLong(int var1);

    public long getLong(String var1);

    public float getFloat(int var1);

    public float getFloat(String var1);

    public double getDouble(int var1);

    public double getDouble(String var1);

    public void setString(int var1, String var2);

    public void setString(String var1, String var2);

    public void setInt(int var1, int var2);

    public void setInt(String var1, int var2);

    public void setLong(int var1, long var2);

    public void setLong(String var1, long var2);

    public void setFloat(int var1, float var2);

    public void setFloat(String var1, float var2);

    public void setDouble(int var1, double var2);

    public void setDouble(String var1, double var2);

    public int getColumnCount();

    public int getColumnType(String var1);

    public int getColumnType(int var1);

    public int[] getColumnTypes();

    public String getColumnTitle(int var1);

    public String[] getColumnTitles();

    public void write(PrintWriter var1);

    public void print();
}

class LongList implements Iterable<Long>
{
    protected int count;
    protected long[] data;

    public LongList()
    {
        this.data = new long[10];
    }

    public LongList(int length)
    {
        this.data = new long[length];
    }

    public LongList(int[] source)
    {
        this.count = source.length;
        this.data = new long[this.count];
        System.arraycopy(source, 0, this.data, 0, this.count);
    }

    public LongList(Iterable<Object> iter)
    {
        this(10);
        for (Object o : iter)
        {
            if (o == null)
            {
                this.append(0L);
                continue;
            }
            if (o instanceof Number)
            {
                this.append(((Number) o).intValue());
                continue;
            }
            this.append(PApplet.parseInt(o.toString().trim()));
        }
        this.crop();
    }

    public /* varargs */ LongList(Object... items)
    {
        boolean missingValue = false;
        this.count = items.length;
        this.data = new long[this.count];
        int index = 0;
        for (Object o : items)
        {
            int value = 0;
            if (o != null)
            {
                value = o instanceof Number ? ((Number) o).intValue() : PApplet.parseInt(o.toString().trim(), 0);
            }
            this.data[index++] = value;
        }
    }

    public static LongList fromRange(int stop)
    {
        return LongList.fromRange(0, stop);
    }

    public static LongList fromRange(int start, int stop)
    {
        int count = stop - start;
        LongList newbie = new LongList(count);
        for (int i = 0; i < count; ++i)
        {
            newbie.set(i, start + i);
        }
        return newbie;
    }

    private void crop()
    {
        if (this.count != this.data.length)
        {
            this.data = PApplet.subset(this.data, 0, this.count);
        }
    }

    public int size()
    {
        return this.count;
    }

    public void resize(int length)
    {
        if (length > this.data.length)
        {
            long[] temp = new long[length];
            System.arraycopy(this.data, 0, temp, 0, this.count);
            this.data = temp;
        }
        else if (length > this.count)
        {
            Arrays.fill(this.data, this.count, length, 0L);
        }
        this.count = length;
    }

    public void clear()
    {
        this.count = 0;
    }

    public long get(int index)
    {
        if (index >= this.count)
        {
            throw new ArrayIndexOutOfBoundsException(index);
        }
        return this.data[index];
    }

    public void set(int index, int what)
    {
        if (index >= this.count)
        {
            this.data = PApplet.expand(this.data, index + 1);
            for (int i = this.count; i < index; ++i)
            {
                this.data[i] = 0L;
            }
            this.count = index + 1;
        }
        this.data[index] = what;
    }

    public void push(int value)
    {
        this.append(value);
    }

    public long pop()
    {
        if (this.count == 0)
        {
            throw new RuntimeException("Can't call pop() on an empty list");
        }
        long value = this.get(this.count - 1);
        --this.count;
        return value;
    }

    public long remove(int index)
    {
        if (index < 0 || index >= this.count)
        {
            throw new ArrayIndexOutOfBoundsException(index);
        }
        long entry = this.data[index];
        for (int i = index; i < this.count - 1; ++i)
        {
            this.data[i] = this.data[i + 1];
        }
        --this.count;
        return entry;
    }

    public int removeValue(int value)
    {
        int index = this.index(value);
        if (index != -1)
        {
            this.remove(index);
            return index;
        }
        return -1;
    }

    public int removeValues(int value)
    {
        int ii = 0;
        for (int i = 0; i < this.count; ++i)
        {
            if (this.data[i] == (long) value)
                continue;
            this.data[ii++] = this.data[i];
        }
        int removed = this.count - ii;
        this.count = ii;
        return removed;
    }

    public void append(long value)
    {
        if (this.count == this.data.length)
        {
            this.data = PApplet.expand(this.data);
        }
        this.data[this.count++] = value;
    }

    public void append(int[] values)
    {
        for (int v : values)
        {
            this.append(v);
        }
    }

    public void append(LongList list)
    {
        for (long v : list.values())
        {
            this.append(v);
        }
    }

    public void appendUnique(int value)
    {
        if (!this.hasValue(value))
        {
            this.append(value);
        }
    }

    public void insert(int index, long value)
    {
        this.insert(index, new long[] { value });
    }

    public void insert(int index, long[] values)
    {
        if (index < 0)
        {
            throw new IllegalArgumentException("insert() index cannot be negative: it was " + index);
        }
        if (index >= this.data.length)
        {
            throw new IllegalArgumentException("insert() index " + index + " is past the end of this list");
        }
        long[] temp = new long[this.count + values.length];
        System.arraycopy(this.data, 0, temp, 0, Math.min(this.count, index));
        System.arraycopy(values, 0, temp, index, values.length);
        System.arraycopy(this.data, index, temp, index + values.length, this.count - index);
        this.count += values.length;
        this.data = temp;
    }

    public void insert(int index, LongList list)
    {
        this.insert(index, list.values());
    }

    public int index(int what)
    {
        for (int i = 0; i < this.count; ++i)
        {
            if (this.data[i] != (long) what)
                continue;
            return i;
        }
        return -1;
    }

    public boolean hasValue(int value)
    {
        for (int i = 0; i < this.count; ++i)
        {
            if (this.data[i] != (long) value)
                continue;
            return true;
        }
        return false;
    }

    public void increment(int index)
    {
        if (this.count <= index)
        {
            this.resize(index + 1);
        }
        long[] arrl = this.data;
        int n = index;
        arrl[n] = arrl[n] + 1L;
    }

    private void boundsProblem(int index, String method)
    {
        String msg = String.format("The list size is %d. You cannot %s() to element %d.", this.count, method, index);
        throw new ArrayIndexOutOfBoundsException(msg);
    }

    public void add(int index, int amount)
    {
        if (index < this.count)
        {
            long[] arrl = this.data;
            int n = index;
            arrl[n] = arrl[n] + (long) amount;
        }
        else
        {
            this.boundsProblem(index, "add");
        }
    }

    public void sub(int index, int amount)
    {
        if (index < this.count)
        {
            long[] arrl = this.data;
            int n = index;
            arrl[n] = arrl[n] - (long) amount;
        }
        else
        {
            this.boundsProblem(index, "sub");
        }
    }

    public void mult(int index, int amount)
    {
        if (index < this.count)
        {
            long[] arrl = this.data;
            int n = index;
            arrl[n] = arrl[n] * (long) amount;
        }
        else
        {
            this.boundsProblem(index, "mult");
        }
    }

    public void div(int index, int amount)
    {
        if (index < this.count)
        {
            long[] arrl = this.data;
            int n = index;
            arrl[n] = arrl[n] / (long) amount;
        }
        else
        {
            this.boundsProblem(index, "div");
        }
    }

    private void checkMinMax(String functionName)
    {
        if (this.count == 0)
        {
            String msg = String.format("Cannot use %s() on an empty %s.", functionName,
                                       this.getClass().getSimpleName());
            throw new RuntimeException(msg);
        }
    }

    public long min()
    {
        this.checkMinMax("min");
        long outgoing = this.data[0];
        for (int i = 1; i < this.count; ++i)
        {
            if (this.data[i] >= outgoing)
                continue;
            outgoing = this.data[i];
        }
        return outgoing;
    }

    public int minIndex()
    {
        this.checkMinMax("minIndex");
        long value = this.data[0];
        int index = 0;
        for (int i = 1; i < this.count; ++i)
        {
            if (this.data[i] >= value)
                continue;
            value = this.data[i];
            index = i;
        }
        return index;
    }

    public long max()
    {
        this.checkMinMax("max");
        long outgoing = this.data[0];
        for (int i = 1; i < this.count; ++i)
        {
            if (this.data[i] <= outgoing)
                continue;
            outgoing = this.data[i];
        }
        return outgoing;
    }

    public int maxIndex()
    {
        this.checkMinMax("maxIndex");
        long value = this.data[0];
        int index = 0;
        for (int i = 1; i < this.count; ++i)
        {
            if (this.data[i] <= value)
                continue;
            value = this.data[i];
            index = i;
        }
        return index;
    }

    public int sum()
    {
        long amount = this.sumLong();
        if (amount > Integer.MAX_VALUE)
        {
            throw new RuntimeException("sum() exceeds 2147483647, use sumLong()");
        }
        if (amount < Integer.MIN_VALUE)
        {
            throw new RuntimeException("sum() less than -2147483648, use sumLong()");
        }
        return (int) amount;
    }

    public long sumLong()
    {
        long sum = 0L;
        for (int i = 0; i < this.count; ++i)
        {
            sum += this.data[i];
        }
        return sum;
    }

    public void sort()
    {
        Arrays.sort(this.data, 0, this.count);
    }

    public void sortReverse()
    {
        new Sort()
        {

            @Override
            public int size()
            {
                return LongList.this.count;
            }

            @Override
            public int compare(int a, int b)
            {
                long diff = LongList.this.data[b] - LongList.this.data[a];
                return diff == 0L ? 0 : (diff < 0L ? -1 : 1);
            }

            @Override
            public void swap(int a, int b)
            {
                long temp = LongList.this.data[a];
                LongList.this.data[a] = LongList.this.data[b];
                LongList.this.data[b] = temp;
            }
        } .run();
    }

    public void reverse()
    {
        int ii = this.count - 1;
        for (int i = 0; i < this.count / 2; ++i)
        {
            long t = this.data[i];
            this.data[i] = this.data[ii];
            this.data[ii] = t;
            --ii;
        }
    }

    public void shuffle()
    {
        Random r = new Random();
        int num = this.count;
        while (num > 1)
        {
            int value = r.nextInt(num);
            long temp = this.data[--num];
            this.data[num] = this.data[value];
            this.data[value] = temp;
        }
    }

    public void shuffle(PApplet sketch)
    {
        int num = this.count;
        while (num > 1)
        {
            int value = (int) sketch.random(num);
            long temp = this.data[--num];
            this.data[num] = this.data[value];
            this.data[value] = temp;
        }
    }

    public LongList copy()
    {
        LongList outgoing = new LongList(new Object[] { this.data });
        outgoing.count = this.count;
        return outgoing;
    }

    public long[] values()
    {
        this.crop();
        return this.data;
    }

    @Override
    public Iterator<Long> iterator()
    {
        return new Iterator<Long>()
        {
            int index = -1;

            @Override
            public void remove()
            {
                LongList.this.remove(this.index);
                --this.index;
            }

            @Override
            public Long next()
            {
                return LongList.this.data[++this.index];
            }

            @Override
            public boolean hasNext()
            {
                return this.index + 1 < LongList.this.count;
            }
        };
    }

    public int[] array()
    {
        return this.array(null);
    }

    public int[] array(int[] array)
    {
        if (array == null || array.length != this.count)
        {
            array = new int[this.count];
        }
        System.arraycopy(this.data, 0, array, 0, this.count);
        return array;
    }

    public FloatList getPercent()
    {
        double sum = 0.0;
        int[] arrn = this.array();
        int n = arrn.length;
        for (int i = 0; i < n; ++i)
        {
            float value = arrn[i];
            sum += (double) value;
        }
        FloatList outgoing = new FloatList(this.count);
        for (int i = 0; i < this.count; ++i)
        {
            double percent = (double) this.data[i] / sum;
            outgoing.set(i, (float) percent);
        }
        return outgoing;
    }

    public LongList getSubset(int start)
    {
        return this.getSubset(start, this.count - start);
    }

    public LongList getSubset(int start, int num)
    {
        int[] subset = new int[num];
        System.arraycopy(this.data, start, subset, 0, num);
        return new LongList(subset);
    }

    public String join(String separator)
    {
        if (this.count == 0)
        {
            return "";
        }
        StringBuilder sb = new StringBuilder();
        sb.append(this.data[0]);
        for (int i = 1; i < this.count; ++i)
        {
            sb.append(separator);
            sb.append(this.data[i]);
        }
        return sb.toString();
    }

    public void print()
    {
        for (int i = 0; i < this.count; ++i)
        {
            System.out.format("[%d] %d%n", i, this.data[i]);
        }
    }

    public void write(PrintWriter writer)
    {
        for (int i = 0; i < this.count; ++i)
        {
            writer.println(this.data[i]);
        }
        writer.flush();
    }

    public String toJSON()
    {
        return "[ " + this.join(", ") + " ]";
    }

    public String toString()
    {
        return this.getClass().getSimpleName() + " size=" + this.size() + " " + this.toJSON();
    }

}

class LongDict
{
    protected int count;
    protected String[] keys;
    protected long[] values;
    private HashMap<String, Integer> indices = new HashMap();

    public LongDict()
    {
        this.count = 0;
        this.keys = new String[10];
        this.values = new long[10];
    }

    public LongDict(int length)
    {
        this.count = 0;
        this.keys = new String[length];
        this.values = new long[length];
    }

    public LongDict(String[] keys, long[] values)
    {
        if (keys.length != values.length)
        {
            throw new IllegalArgumentException("key and value arrays must be the same length");
        }
        this.keys = keys;
        this.values = values;
        this.count = keys.length;
        for (int i = 0; i < this.count; ++i)
        {
            this.indices.put(keys[i], i);
        }
    }

    public LongDict(Object[][] pairs)
    {
        this.count = pairs.length;
        this.keys = new String[this.count];
        this.values = new long[this.count];
        for (int i = 0; i < this.count; ++i)
        {
            this.keys[i] = (String) pairs[i][0];
            this.values[i] = ((Integer) pairs[i][1]).intValue();
            this.indices.put(this.keys[i], i);
        }
    }

    public int size()
    {
        return this.count;
    }

    public void resize(int length)
    {
        if (length > this.count)
        {
            throw new IllegalArgumentException("resize() can only be used to shrink the dictionary");
        }
        if (length < 1)
        {
            throw new IllegalArgumentException("resize(" + length + ") is too small, use 1 or higher");
        }
        String[] newKeys = new String[length];
        long[] newValues = new long[length];
        PApplet.arrayCopy(this.keys, newKeys, length);
        PApplet.arrayCopy(this.values, newValues, length);
        this.keys = newKeys;
        this.values = newValues;
        this.count = length;
        this.resetIndices();
    }

    public void clear()
    {
        this.count = 0;
        this.indices = new HashMap();
    }

    private void resetIndices()
    {
        this.indices = new HashMap(this.count);
        for (int i = 0; i < this.count; ++i)
        {
            this.indices.put(this.keys[i], i);
        }
    }

    public Iterable<Entry> entries()
    {
        return new Iterable<Entry>()
        {

            @Override
            public Iterator<Entry> iterator()
            {
                return LongDict.this.entryIterator();
            }
        };
    }

    public Iterator<Entry> entryIterator()
    {
        return new Iterator<Entry>()
        {
            int index = -1;

            @Override
            public void remove()
            {
                LongDict.this.removeIndex(this.index);
                --this.index;
            }

            @Override
            public Entry next()
            {
                ++this.index;
                Entry e = new Entry(LongDict.this.keys[this.index], LongDict.this.values[this.index]);
                return e;
            }

            @Override
            public boolean hasNext()
            {
                return this.index + 1 < LongDict.this.size();
            }
        };
    }

    public String key(int index)
    {
        return this.keys[index];
    }

    protected void crop()
    {
        if (this.count != this.keys.length)
        {
            this.keys = PApplet.subset(this.keys, 0, this.count);
            this.values = PApplet.subset(this.values, 0, this.count);
        }
    }

    public Iterable<String> keys()
    {
        return new Iterable<String>()
        {

            @Override
            public Iterator<String> iterator()
            {
                return LongDict.this.keyIterator();
            }
        };
    }

    public Iterator<String> keyIterator()
    {
        return new Iterator<String>()
        {
            int index = -1;

            @Override
            public void remove()
            {
                LongDict.this.removeIndex(this.index);
                --this.index;
            }

            @Override
            public String next()
            {
                return LongDict.this.key(++this.index);
            }

            @Override
            public boolean hasNext()
            {
                return this.index + 1 < LongDict.this.size();
            }
        };
    }

    public String[] keyArray()
    {
        this.crop();
        return this.keyArray(null);
    }

    public String[] keyArray(String[] outgoing)
    {
        if (outgoing == null || outgoing.length != this.count)
        {
            outgoing = new String[this.count];
        }
        System.arraycopy(this.keys, 0, outgoing, 0, this.count);
        return outgoing;
    }

    public long value(int index)
    {
        return this.values[index];
    }

    public Iterable<Long> values()
    {
        return new Iterable<Long>()
        {

            @Override
            public Iterator<Long> iterator()
            {
                return LongDict.this.valueIterator();
            }
        };
    }

    public Iterator<Long> valueIterator()
    {
        return new Iterator<Long>()
        {
            int index = -1;

            @Override
            public void remove()
            {
                LongDict.this.removeIndex(this.index);
                --this.index;
            }

            @Override
            public Long next()
            {
                return LongDict.this.value(++this.index);
            }

            @Override
            public boolean hasNext()
            {
                return this.index + 1 < LongDict.this.size();
            }
        };
    }

    public int[] valueArray()
    {
        this.crop();
        return this.valueArray(null);
    }

    public int[] valueArray(int[] array)
    {
        if (array == null || array.length != this.size())
        {
            array = new int[this.count];
        }
        System.arraycopy(this.values, 0, array, 0, this.count);
        return array;
    }

    public long get(String key)
    {
        int index = this.index(key);
        if (index == -1)
        {
            throw new IllegalArgumentException("No key named '" + key + "'");
        }
        return this.values[index];
    }

    public long get(String key, long alternate)
    {
        int index = this.index(key);
        if (index == -1)
        {
            return alternate;
        }
        return this.values[index];
    }

    public void set(String key, long amount)
    {
        int index = this.index(key);
        if (index == -1)
        {
            this.create(key, amount);
        }
        else
        {
            this.values[index] = amount;
        }
    }

    public void setIndex(int index, String key, long value)
    {
        if (index < 0 || index >= this.count)
        {
            throw new ArrayIndexOutOfBoundsException(index);
        }
        this.keys[index] = key;
        this.values[index] = value;
    }

    public boolean hasKey(String key)
    {
        return this.index(key) != -1;
    }

    public void increment(String key)
    {
        this.add(key, 1L);
    }

    public void increment(LongDict dict)
    {
        for (int i = 0; i < dict.count; ++i)
        {
            this.add(dict.key(i), dict.value(i));
        }
    }

    public void add(String key, long amount)
    {
        int index = this.index(key);
        if (index == -1)
        {
            this.create(key, amount);
        }
        else
        {
            long[] arrl = this.values;
            int n = index;
            arrl[n] = arrl[n] + amount;
        }
    }

    public void sub(String key, long amount)
    {
        this.add(key, -amount);
    }

    public void mult(String key, long amount)
    {
        int index = this.index(key);
        if (index != -1)
        {
            long[] arrl = this.values;
            int n = index;
            arrl[n] = arrl[n] * amount;
        }
    }

    public void div(String key, long amount)
    {
        int index = this.index(key);
        if (index != -1)
        {
            long[] arrl = this.values;
            int n = index;
            arrl[n] = arrl[n] / amount;
        }
    }

    private void checkMinMax(String functionName)
    {
        if (this.count == 0)
        {
            String msg = String.format("Cannot use %s() on an empty %s.", functionName,
                                       this.getClass().getSimpleName());
            throw new RuntimeException(msg);
        }
    }

    public int minIndex()
    {
        if (this.count == 0)
        {
            return -1;
        }
        int index = 0;
        long value = this.values[0];
        for (int i = 1; i < this.count; ++i)
        {
            if (this.values[i] >= value)
                continue;
            index = i;
            value = this.values[i];
        }
        return index;
    }

    public String minKey()
    {
        this.checkMinMax("minKey");
        int index = this.minIndex();
        if (index == -1)
        {
            return null;
        }
        return this.keys[index];
    }

    public long minValue()
    {
        this.checkMinMax("minValue");
        return this.values[this.minIndex()];
    }

    public int maxIndex()
    {
        if (this.count == 0)
        {
            return -1;
        }
        int index = 0;
        long value = this.values[0];
        for (int i = 1; i < this.count; ++i)
        {
            if (this.values[i] <= value)
                continue;
            index = i;
            value = this.values[i];
        }
        return index;
    }

    public String maxKey()
    {
        int index = this.maxIndex();
        if (index == -1)
        {
            return null;
        }
        return this.keys[index];
    }

    public long maxValue()
    {
        this.checkMinMax("maxIndex");
        return this.values[this.maxIndex()];
    }

    public long sum()
    {
        long sum = 0L;
        for (int i = 0; i < this.count; ++i)
        {
            sum += this.values[i];
        }
        return sum;
    }

    public int index(String what)
    {
        Integer found = this.indices.get(what);
        return found == null ? -1 : found;
    }

    protected void create(String what, long much)
    {
        if (this.count == this.keys.length)
        {
            this.keys = PApplet.expand(this.keys);
            this.values = PApplet.expand(this.values);
        }
        this.indices.put(what, this.count);
        this.keys[this.count] = what;
        this.values[this.count] = much;
        ++this.count;
    }

    public long remove(String key)
    {
        int index = this.index(key);
        if (index == -1)
        {
            throw new NoSuchElementException("'" + key + "' not found");
        }
        long value = this.values[index];
        this.removeIndex(index);
        return value;
    }

    public long removeIndex(int index)
    {
        if (index < 0 || index >= this.count)
        {
            throw new ArrayIndexOutOfBoundsException(index);
        }
        long value = this.values[index];
        this.indices.remove(this.keys[index]);
        for (int i = index; i < this.count - 1; ++i)
        {
            this.keys[i] = this.keys[i + 1];
            this.values[i] = this.values[i + 1];
            this.indices.put(this.keys[i], i);
        }
        --this.count;
        this.keys[this.count] = null;
        this.values[this.count] = 0L;
        return value;
    }

    public void swap(int a, int b)
    {
        String tkey = this.keys[a];
        long tvalue = this.values[a];
        this.keys[a] = this.keys[b];
        this.values[a] = this.values[b];
        this.keys[b] = tkey;
        this.values[b] = tvalue;
    }

    public void sortKeys()
    {
        this.sortImpl(true, false, true);
    }

    public void sortKeysReverse()
    {
        this.sortImpl(true, true, true);
    }

    public void sortValues()
    {
        this.sortValues(true);
    }

    public void sortValues(boolean stable)
    {
        this.sortImpl(false, false, stable);
    }

    public void sortValuesReverse()
    {
        this.sortValuesReverse(true);
    }

    public void sortValuesReverse(boolean stable)
    {
        this.sortImpl(false, true, stable);
    }

    protected void sortImpl(final boolean useKeys, final boolean reverse, final boolean stable)
    {
        Sort s = new Sort()
        {

            @Override
            public int size()
            {
                return LongDict.this.count;
            }

            @Override
            public int compare(int a, int b)
            {
                long diff = 0L;
                if (useKeys)
                {
                    diff = LongDict.this.keys[a].compareToIgnoreCase(LongDict.this.keys[b]);
                    if (diff == 0L)
                    {
                        diff = LongDict.this.values[a] - LongDict.this.values[b];
                    }
                }
                else
                {
                    diff = LongDict.this.values[a] - LongDict.this.values[b];
                    if (diff == 0L && stable)
                    {
                        diff = LongDict.this.keys[a].compareToIgnoreCase(LongDict.this.keys[b]);
                    }
                }
                if (diff == 0L)
                {
                    return 0;
                }
                if (reverse)
                {
                    return diff < 0L ? 1 : -1;
                }
                return diff < 0L ? -1 : 1;
            }

            @Override
            public void swap(int a, int b)
            {
                LongDict.this.swap(a, b);
            }
        };
        s.run();
        this.resetIndices();
    }

    public FloatDict getPercent()
    {
        double sum = this.sum();
        FloatDict outgoing = new FloatDict();
        for (int i = 0; i < this.size(); ++i)
        {
            double percent = (double) this.value(i) / sum;
            outgoing.set(this.key(i), (float) percent);
        }
        return outgoing;
    }

    public LongDict copy()
    {
        LongDict outgoing = new LongDict(this.count);
        System.arraycopy(this.keys, 0, outgoing.keys, 0, this.count);
        System.arraycopy(this.values, 0, outgoing.values, 0, this.count);
        for (int i = 0; i < this.count; ++i)
        {
            outgoing.indices.put(this.keys[i], i);
        }
        outgoing.count = this.count;
        return outgoing;
    }

    public void print()
    {
        for (int i = 0; i < this.size(); ++i)
        {
            System.out.println(this.keys[i] + " = " + this.values[i]);
        }
    }

    public void write(PrintWriter writer)
    {
        for (int i = 0; i < this.count; ++i)
        {
            writer.println(this.keys[i] + "\t" + this.values[i]);
        }
        writer.flush();
    }

    public String toJSON()
    {
        StringList items = new StringList();
        for (int i = 0; i < this.count; ++i)
        {
            items.append(JSONObject.quote(this.keys[i]) + ": " + this.values[i]);
        }
        return "{ " + items.join(", ") + " }";
    }

    public String toString()
    {
        return this.getClass().getSimpleName() + " size=" + this.size() + " " + this.toJSON();
    }

    public class Entry
    {
        public String key;
        public long value;

        Entry(String key, long value)
        {
            this.key = key;
            this.value = value;
        }
    }

}
