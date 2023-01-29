import java.util.*;

public class Seed2 {
    public static void main(String[] args) {
        int[] arr = new int[1000000000];
        Scanner sc = new Scanner(System.in);
        String result;
        long lo = 1;
        long hi = 2000000000;
        long num;
        while (lo < hi) {
            num = (lo + hi) / 2;
            System.out.println(num);
            result = sc.nextLine();
            if (result.equals("FLOATS"))
                hi = num;
            else if (result.equals("SINKS"))
                lo = num + 1;
            else
                break;
        }
    }
}
