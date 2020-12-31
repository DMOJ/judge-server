import java.math.BigInteger;
import java.util.Scanner;
public class aplusb {
    public static void main(String[] args) {
        Scanner in = new Scanner(System.in);
        int N = in.nextInt();
        for(int i=0;i<N;i++)
            System.out.println(new BigInteger(in.next()).add(new BigInteger(in.next())));        
    }
}
