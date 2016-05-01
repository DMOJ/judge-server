import os

from dmoj.executors.clr_executor import CLRExecutor
from dmoj.executors.utils import test_executor
from dmoj.judgeenv import env


class Executor(CLRExecutor):
    extension = 'cs'
    compiler = 'csc'


def initialize(sandbox=True):
    # TODO: sandbox is ignored
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
