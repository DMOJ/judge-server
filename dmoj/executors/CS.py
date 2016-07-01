from dmoj.executors.clr_executor import CLRExecutor


class Executor(CLRExecutor):
    ext = '.cs'
    name = 'CS'
    compiler = 'csc'

    test_program = '''\
using System;

class test {
    public static void Main(string[] args) {
        Console.WriteLine(Console.ReadLine());
    }
}'''
