from dmoj.executors.script_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = 'pl'
    command = 'swipl'
    test_program = """
    :- set_prolog_flag(verbose,silent).
    :- prompt(_, '').
    :- use_module(library(readutil)).

    main:-
        process,
        halt.

    process:-
        write('echo: Hello, World!'), nl,
        true.

    :- main.
"""

    def get_cmdline(self, **kwargs):
        return [self.get_command(), '--goal=main', '-c', self._code]
