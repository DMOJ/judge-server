import difflib
from typing import List

import pygments.formatters
import pygments.lexers

from dmoj.commands.base_command import Command


class DifferenceCommand(Command):
    name = 'diff'
    help = 'Shows difference between two files.'

    def _populate_parser(self) -> None:
        self.arg_parser.add_argument('id_or_source_1', help='id or path of first source', metavar='<source 1>')
        self.arg_parser.add_argument('id_or_source_2', help='id or path of second source', metavar='<source 2>')

    def get_data(self, id_or_source: str) -> List[str]:
        try:
            _, _, src, _, _ = self.get_submission_data(int(id_or_source))
        except ValueError:
            src = self.get_source(id_or_source)

        return src.splitlines()

    def execute(self, line: str) -> None:
        args = self.arg_parser.parse_args(line)

        file1: str = args.id_or_source_1
        file2: str = args.id_or_source_2

        data1 = self.get_data(file1)
        data2 = self.get_data(file2)

        difference = list(difflib.unified_diff(data1, data2, fromfile=file1, tofile=file2, lineterm=''))
        if not difference:
            print('no difference\n')
        else:
            file_diff = '\n'.join(difference)
            print(
                pygments.highlight(file_diff, pygments.lexers.DiffLexer(), pygments.formatters.Terminal256Formatter())
            )
