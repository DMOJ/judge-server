using System;
using System.Text;

public class Example
{
    public static void Main()
    {
        StringBuilder sb = new StringBuilder(15, 15);
        sb.Append("Substring #1 ");
        sb.Insert(0, "Substring #2 ", 1);
    }
}
