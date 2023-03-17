import sys

from dmoj import judgeenv
from dmoj.commands.base_command import Command


class LocateCommand(Command):
    name = 'locate'
    help = 'Locates the folders for problems available to be graded on this judge.'

    def _populate_parser(self) -> None:
        self.arg_parser.add_argument('problems', nargs='+', help='problems to locate')

    def execute(self, line: str) -> None:
        args = self.arg_parser.parse_args(line)

        problems = args.problems
        for problem in problems:
            root = judgeenv.get_problem_root(problem)
            if root is None:
                print(f'{problem} is not a valid problem, skipping', file=sys.stderr)
            else:
                print(root)
