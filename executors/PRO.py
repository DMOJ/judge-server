from .base_executor import ScriptExecutor
from judgeenv import env


class Executor(ScriptExecutor):
    ext = '.pl'
    name = 'PRO'
    command = env['runtime'].get('swipl')
    test_program = '''
    :- set_prolog_flag(verbose,silent).
    :- prompt(_, '').
    :- use_module(library(readutil)).

    main:-
        process,
        halt.

    process:-
        write('echo: Hello, World!'), nl.
        true.

    :- main.
'''
    syscalls = ['nanosleep']

    fs = ['.*\.(?:so|pl|pro)', '/etc/localtime$', '/usr/lib/', command]

    def get_cmdline(self):
        return [self.get_command(), '--goal=main', '-c', self._code]

initialize = Executor.initialize
