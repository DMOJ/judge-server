import re
from itertools import zip_longest
from operator import itemgetter

from dmoj import judgeenv
from dmoj.commands.base_command import Command
from dmoj.error import InvalidCommandException


class ListProblemsCommand(Command):
    name = 'problems'
    help = 'Lists the problems available to be graded on this judge.'

    def _populate_parser(self):
        self.arg_parser.add_argument('filter', nargs='?', help='regex filter for problem names (optional)')
        self.arg_parser.add_argument('-l', '--limit', type=int, help='limit number of results', metavar='<limit>')

    def execute(self, line):
        _args = self.arg_parser.parse_args(line)

        if _args.limit is not None and _args.limit <= 0:
            raise InvalidCommandException('--limit must be >= 0')

        all_problems = judgeenv.get_supported_problems()

        if _args.filter:
            r = re.compile(_args.filter)
            all_problems = list(filter(lambda x: r.match(x[0]) is not None, all_problems))

        if _args.limit:
            all_problems = all_problems[:_args.limit]

        if len(all_problems):
            problems = iter(map(itemgetter(0), all_problems))
            max_len = max(len(p[0]) for p in all_problems)
            for row in zip_longest(*[problems] * 4, fillvalue=''):
                print(' '.join(('%*s' % (-max_len, row[i])) for i in range(4)))
            print()
        else:
            raise InvalidCommandException('No problems matching filter found.')
