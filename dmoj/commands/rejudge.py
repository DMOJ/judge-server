from dmoj.commands.base_command import Command


class RejudgeCommand(Command):
    name = 'rejudge'
    help = 'Rejudge a submission.'

    def _populate_parser(self):
        self.arg_parser.add_argument('submission_id', type=int, help='id of submission to rejudge')

    def execute(self, line):
        args = self.arg_parser.parse_args(line)
        problem, lang, src, tl, ml = self.get_submission_data(args.submission_id)

        self.judge.begin_grading(self.judge.submission_id_counter, problem, lang, src, tl, ml, False, False,
                                 blocking=True)
