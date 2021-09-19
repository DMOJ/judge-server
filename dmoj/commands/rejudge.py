from dmoj.commands.base_command import Command
from dmoj.judge import Submission


class RejudgeCommand(Command):
    name = 'rejudge'
    help = 'Rejudge a submission.'

    def _populate_parser(self) -> None:
        self.arg_parser.add_argument('submission_id', type=int, help='id of submission to rejudge')

    def execute(self, line: str) -> None:
        args = self.arg_parser.parse_args(line)
        problem_id, lang, src, tl, ml = self.get_submission_data(args.submission_id)

        self.judge.begin_grading(
            Submission(self.judge.submission_id_counter, problem_id, lang, src, tl, ml, False, {}),
            blocking=True,
            report=print,
        )
