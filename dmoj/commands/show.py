from typing import Tuple

import pygments.formatters
import pygments.lexers
from pygments.lexer import Lexer

from dmoj.commands.base_command import Command


class ShowCommand(Command):
    name = 'show'
    help = 'Shows file based on submission ID or filename.'

    def _populate_parser(self) -> None:
        self.arg_parser.add_argument('id_or_source', help='id or path of submission to show', metavar='<source>')

    def get_data(self, id_or_source: str) -> Tuple[str, Lexer]:
        try:
            sub_id = int(id_or_source)
        except ValueError:
            src = self.get_source(id_or_source)
            lexer = pygments.lexers.get_lexer_for_filename(id_or_source)
        else:
            _, lang, src, _, _ = self.get_submission_data(sub_id)

            # TODO: after executor->extension mapping is built-in to the judge, redo this
            if lang in ['PY2', 'PYPY2']:
                lexer = pygments.lexers.PythonLexer()
            elif lang in ['PY3', 'PYPY3']:
                lexer = pygments.lexers.Python3Lexer()
            else:
                lexer = pygments.lexers.guess_lexer(src)

        return src, lexer

    def execute(self, line: str) -> None:
        args = self.arg_parser.parse_args(line)
        data, lexer = self.get_data(args.id_or_source)

        print(pygments.highlight(data, lexer, pygments.formatters.Terminal256Formatter()))
