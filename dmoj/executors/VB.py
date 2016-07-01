from dmoj.executors.clr_executor import CLRExecutor


class Executor(CLRExecutor):
    ext = '.vb'
    name = 'VB'

    compiler = 'vbc'
    compile_args = ['/nologo', '/out:{exe}', '/optimize+', '{source}']
    test_program = '''\
Imports System

Public Module modmain
   Sub Main()
     Console.WriteLine(Console.ReadLine())
   End Sub
End Module
'''
