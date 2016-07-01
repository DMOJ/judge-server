from dmoj.executors.clr_executor import CLRExecutor


class Executor(CLRExecutor):
    ext = '.fs'
    name = 'FS'

    compiler = 'fsc'
    compile_args = ['--nologo', '--out:{exe}', '{source}']

    test_program = '''\
open System
let input = System.Console.ReadLine()
Console.WriteLine(input)
'''
