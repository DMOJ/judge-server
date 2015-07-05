import os
from .clr_executor import CLRExecutor
from executors.utils import test_executor
from judgeenv import env


class Executor(CLRExecutor):
    extension = 'cs'
    compiler = 'csc'


def initialize():
    if 'csc' not in env['runtime']:
        return False
    if not os.path.isfile(env['runtime']['csc']):
        return False
    return test_executor('CS', Executor, '''\
using System;

class test {
    public static void Main(string[] args) {
        Console.WriteLine("Hello, World!");
    }
}''')