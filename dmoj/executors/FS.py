from dmoj.executors.clr_executor import CLRExecutor


class Executor(CLRExecutor):
    ext = '.fs'
    name = 'FS'

    compiler = 'fsc'
    compile_args = ['--nologo', '--out:{exe}', '{source}']
    compiler_time_limit = 20

    command_paths = [
        r'C:\Program Files (x86)\Microsoft SDKs\F#\4.0\Framework\v4.0\Fsc.exe',
        r'C:\Program Files\Microsoft SDKs\F#\4.0\Framework\v4.0\Fsc.exe',
    ]

    test_program = '''\
open System
let input = System.Console.ReadLine()
Console.WriteLine(input)
'''

    @classmethod
    def get_find_first_mapping(cls):
        return {cls.compiler: cls.command_paths}
