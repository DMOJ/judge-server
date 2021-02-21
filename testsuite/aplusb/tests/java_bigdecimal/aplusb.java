import java.math.BigDecimal;
import java.util.Scanner;
public class aplusb {
    public static void main(String[] args) {
        Scanner in = new Scanner(System.in);
        int N = in.nextInt();
        for(int i=0;i<N;i++)
            System.out.println(new BigDecimal(in.next()).add(new BigDecimal(in.next())).toBigInteger());        
    }
}
