import java.util.*;
import java.io.*;

public class aplusb {
    public static void main(String args[]) throws IOException {
        BufferedReader cin = new BufferedReader(new InputStreamReader(System.in));
        int N = Integer.parseInt(cin.readLine());

        for (int i = 0; i < N; i++) {
            String[] line = cin.readLine().split(" ");
            System.out.println(Integer.parseInt(line[0]) + Integer.parseInt(line[1]));
        }
    }
}
