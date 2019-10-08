import argparse
import os
import subprocess
import sys
import tempfile
from collections import OrderedDict
from typing import Dict

from dmoj.error import InvalidCommandException
from dmoj.executors import executors
from dmoj.utils.ansi import print_ansi


class CommandArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        raise InvalidCommandException

    def exit(self, status=0, message=None):
        if message:
            self._print_message(message, sys.stderr)
        raise InvalidCommandException


class Command:
    name = 'command'
    help = ''

    def __init__(self, judge):
        self.judge = judge
        self.arg_parser = CommandArgumentParser(prog=self.name, description=self.help)
        self._populate_parser()

    def get_source(self, source_file):
        try:
            with open(os.path.realpath(source_file)) as f:
                return f.read()
        except Exception as io:
            raise InvalidCommandException(str(io))

    def get_submission_data(self, submission_id):
        # don't wrap around
        if submission_id > 0:
            try:
                return self.judge.graded_submissions[submission_id - 1]
            except IndexError:
                pass

        raise InvalidCommandException("invalid submission '%d'" % submission_id)

    def open_editor(self, lang, src=b''):
        file_suffix = executors[lang].Executor.ext
        editor = os.environ.get('EDITOR')
        if editor:
            with tempfile.NamedTemporaryFile(suffix=file_suffix) as temp:
                temp.write(src)
                temp.flush()
                subprocess.call([editor, temp.name])
                temp.seek(0)
                src = temp.read()
        else:
            print_ansi('#ansi[$EDITOR not set, falling back to stdin](yellow)\n')
            src = []
            try:
                while True:
                    s = input()
                    if s.strip() == ':q':
                        raise EOFError
                    src.append(s)
            except EOFError:  # Ctrl+D
                src = '\n'.join(src)
            except Exception as io:
                raise InvalidCommandException(str(io))
        return src

    def _populate_parser(self):
        pass

    def execute(self, line):
        raise NotImplementedError


commands: Dict[str, Command] = OrderedDict()


def register_command(command):
    commands[command.name] = command
