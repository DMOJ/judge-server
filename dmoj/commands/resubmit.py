from operator import itemgetter

from dmoj import judgeenv
from dmoj.commands.base_command import Command
from dmoj.error import InvalidCommandException
from dmoj.executors import executors


class ResubmitCommand(Command):
    name = 'resubmit'
    help = 'Resubmit a submission with different parameters.'

    def _populate_parser(self):
        self.arg_parser.add_argument('submission_id', type=int, help='id of submission to resubmit')
        self.arg_parser.add_argument('-p', '--problem', help='id of problem to grade', metavar='<problem id>')
        self.arg_parser.add_argument('-l', '--language', help='id of the language to grade in (e.g., PY2)',
                                     metavar='<language id>')
        self.arg_parser.add_argument('-tl', '--time-limit', type=float, help='time limit for grading, in seconds',
                                     metavar='<time limit>')
        self.arg_parser.add_argument('-ml', '--memory-limit', type=int, help='memory limit for grading, in kilobytes',
                                     metavar='<memory limit>')

    def execute(self, line):
        args = self.arg_parser.parse_args(line)

        id, lang, src, tl, ml = self.get_submission_data(args.submission_id)

        id = args.problem or id
        lang = args.language or lang
        tl = args.time_limit or tl
        ml = args.memory_limit or ml

        if id not in map(itemgetter(0), judgeenv.get_supported_problems()):
            raise InvalidCommandException("unknown problem '%s'" % id)
        elif lang not in executors:
            raise InvalidCommandException("unknown language '%s'" % lang)
        elif tl <= 0:
            raise InvalidCommandException('--time-limit must be >= 0')
        elif ml <= 0:
            raise InvalidCommandException('--memory-limit must be >= 0')

        src = self.open_editor(lang, src)

        self.judge.submission_id_counter += 1
        self.judge.graded_submissions.append((id, lang, src, tl, ml))
        self.judge.begin_grading(self.judge.submission_id_counter, id, lang, src, tl, ml, False, False, blocking=True)
