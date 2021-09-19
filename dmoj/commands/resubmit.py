from dmoj import judgeenv
from dmoj.commands.base_command import Command
from dmoj.error import InvalidCommandException
from dmoj.executors import executors
from dmoj.judge import Submission


class ResubmitCommand(Command):
    name = 'resubmit'
    help = 'Resubmit a submission with different parameters.'

    def _populate_parser(self) -> None:
        self.arg_parser.add_argument('submission_id', type=int, help='id of submission to resubmit')
        self.arg_parser.add_argument('-p', '--problem', help='id of problem to grade', metavar='<problem id>')
        self.arg_parser.add_argument(
            '-l', '--language', help='id of the language to grade in (e.g., PY2)', metavar='<language id>'
        )
        self.arg_parser.add_argument(
            '-tl', '--time-limit', type=float, help='time limit for grading, in seconds', metavar='<time limit>'
        )
        self.arg_parser.add_argument(
            '-ml', '--memory-limit', type=int, help='memory limit for grading, in kilobytes', metavar='<memory limit>'
        )

    def execute(self, line: str) -> None:
        args = self.arg_parser.parse_args(line)

        problem_id, lang, src, tl, ml = self.get_submission_data(args.submission_id)

        problem_id = args.problem or problem_id
        lang = args.language or lang
        tl = args.time_limit or tl
        ml = args.memory_limit or ml

        if id not in judgeenv.get_supported_problems():
            raise InvalidCommandException(f"unknown problem '{problem_id}'")
        elif lang not in executors:
            raise InvalidCommandException(f"unknown language '{lang}'")
        elif tl <= 0:
            raise InvalidCommandException('--time-limit must be >= 0')
        elif ml <= 0:
            raise InvalidCommandException('--memory-limit must be >= 0')

        src = self.open_editor(lang, src)

        self.judge.submission_id_counter += 1
        self.judge.graded_submissions.append((problem_id, lang, src, tl, ml))
        try:
            self.judge.begin_grading(
                Submission(self.judge.submission_id_counter, problem_id, lang, src, tl, ml, False, {}),
                blocking=True,
                report=print,
            )
        except KeyboardInterrupt:
            self.judge.abort_grading()
