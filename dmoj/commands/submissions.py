from dmoj.cli import InvalidCommandException
from dmoj.commands.base_command import Command
from dmoj.utils.ansi import ansi_style


class ListSubmissionsCommand(Command):
    name = 'submissions'
    help = 'List past submissions.'

    def _populate_parser(self):
        self.arg_parser.add_argument('-l', '--limit', type=int, help='limit number of results by most recent',
                                     metavar='<limit>')

    def execute(self, line):
        args = self.arg_parser.parse_args(line)

        if args.limit is not None and args.limit <= 0:
            raise InvalidCommandException("--limit must be >= 0")

        submissions = self.judge.graded_submissions if not args.limit else self.judge.graded_submissions[:args.limit]

        for i, (problem, lang, src, tl, ml) in enumerate(submissions):
            print(ansi_style('#ansi[%s](yellow)/#ansi[%s](green) in %s' % (problem, i + 1, lang)))
        print()
