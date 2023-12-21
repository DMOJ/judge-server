import java.io.*;
import java.util.*;
import java.lang.reflect.*;
import sun.misc.Unsafe;

class OffHeapArray {
    private final static int BYTE = 1;
    private long size;
    private long address;

    public OffHeapArray(long size) throws NoSuchFieldException, IllegalAccessException {
        this.size = size;
        address = getUnsafe().allocateMemory(size * BYTE);
    }

    private Unsafe getUnsafe() throws IllegalAccessException, NoSuchFieldException {
        Field f = Unsafe.class.getDeclaredField("theUnsafe");
        f.setAccessible(true);
        return (Unsafe) f.get(null);
    }

    public void set(long i, byte value) throws NoSuchFieldException, IllegalAccessException {
        getUnsafe().putByte(address + i * BYTE, value);
    }

    public int get(long idx) throws NoSuchFieldException, IllegalAccessException {
        return getUnsafe().getByte(address + idx * BYTE);
    }

    public long size() {
        return size;
    }

    public void freeMemory() throws NoSuchFieldException, IllegalAccessException {
        getUnsafe().freeMemory(address);
    }
}

public class HelloWorld {
    public static void main(String[] args) throws Exception {
        OffHeapArray bigarray = new OffHeapArray(64*8*1024*1024);
        for (int i = 0; i < 131072; i++) bigarray.set(i * 4096 + 16, (byte) 1);
        System.out.println("Hello, World!");
    }
}
// Source: https://dmoj.ca/src/5961758
