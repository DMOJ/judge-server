import argparse
import os
import subprocess
import sys
import tempfile
from collections import OrderedDict
from typing import Dict, NoReturn, Optional, TYPE_CHECKING, Tuple

from dmoj.error import InvalidCommandException
from dmoj.executors import executors
from dmoj.utils.ansi import print_ansi

if TYPE_CHECKING:
    from dmoj.cli import LocalJudge

GradedSubmission = Tuple[str, str, str, float, int]


class CommandArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        raise InvalidCommandException

    def exit(self, status: int = 0, message: Optional[str] = None) -> NoReturn:
        if message:
            self._print_message(message, sys.stderr)
        raise InvalidCommandException


class Command:
    name = 'command'
    help = ''

    def __init__(self, judge: 'LocalJudge') -> None:
        self.judge = judge
        self.arg_parser = CommandArgumentParser(prog=self.name, description=self.help)
        self._populate_parser()

    def get_source(self, source_file: str) -> str:
        try:
            with open(os.path.realpath(source_file)) as f:
                return f.read()
        except Exception as io:
            raise InvalidCommandException(str(io))

    def get_submission_data(self, submission_id: int) -> GradedSubmission:
        # don't wrap around
        if submission_id > 0:
            try:
                return self.judge.graded_submissions[submission_id - 1]
            except IndexError:
                pass

        raise InvalidCommandException(f"invalid submission '{submission_id}'")

    def open_editor(self, lang: str, src: str = '') -> str:
        file_suffix = '.' + executors[lang].Executor.ext
        editor = os.environ.get('EDITOR')
        if editor:
            with tempfile.NamedTemporaryFile(mode='w+', suffix=file_suffix) as temp:
                temp.write(src)
                temp.flush()
                subprocess.call([editor, temp.name])
                temp.seek(0)
                src = temp.read()
        else:
            print_ansi('#ansi[$EDITOR not set, falling back to stdin](yellow)\n')
            lines = []
            try:
                while True:
                    s = input()
                    if s.strip() == ':q':
                        raise EOFError
                    lines.append(s)
            except EOFError:  # Ctrl+D
                src = '\n'.join(lines)
            except Exception as io:
                raise InvalidCommandException(str(io))
        return src

    def _populate_parser(self) -> None:
        pass

    def execute(self, line: str) -> Optional[int]:
        raise NotImplementedError


commands: Dict[str, Command] = OrderedDict()


def register_command(command: Command) -> None:
    commands[command.name] = command
