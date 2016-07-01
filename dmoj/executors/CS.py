import os

from dmoj.executors.clr_executor import CLRExecutor
from dmoj.executors.utils import test_executor
from dmoj.judgeenv import env


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

initialize = Executor.initialize
