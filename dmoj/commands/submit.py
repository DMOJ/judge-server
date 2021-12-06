from typing import Optional

from dmoj import executors, judgeenv
from dmoj.commands.base_command import Command
from dmoj.error import InvalidCommandException
from dmoj.judge import Submission


class SubmitCommand(Command):
    name = 'submit'
    help = 'Grades a submission.'

    def _populate_parser(self) -> None:
        self.arg_parser.add_argument('problem_id', help='id of problem to grade')
        self.arg_parser.add_argument(
            'language_id', nargs='?', default=None, help='id of the language to grade in (e.g., PY2)'
        )
        self.arg_parser.add_argument(
            'source_file', nargs='?', default=None, help='path to submission source (optional)'
        )
        self.arg_parser.add_argument(
            '-tl',
            '--time-limit',
            type=float,
            help='time limit for grading, in seconds',
            default=2.0,
            metavar='<time limit>',
        )
        self.arg_parser.add_argument(
            '-ml',
            '--memory-limit',
            type=int,
            help='memory limit for grading, in kilobytes',
            default=65536,
            metavar='<memory limit>',
        )

    def execute(self, line: str) -> None:
        args = self.arg_parser.parse_args(line)

        problem_id: str = args.problem_id
        language_id: Optional[str] = args.language_id
        time_limit: float = args.time_limit
        memory_limit: int = args.memory_limit
        source_file: Optional[str] = args.source_file

        if language_id not in executors.executors:
            source_file = language_id
            language_id = None  # source file / language id optional

        if problem_id not in judgeenv.get_supported_problems():
            raise InvalidCommandException(f"unknown problem '{problem_id}'")
        elif not language_id:
            if source_file:
                language_id = executors.from_filename(source_file).Executor.name
            else:
                raise InvalidCommandException('no language is selected')
        elif language_id not in executors.executors:
            raise InvalidCommandException(f"unknown language '{language_id}'")
        elif time_limit <= 0:
            raise InvalidCommandException('--time-limit must be >= 0')
        elif memory_limit <= 0:
            raise InvalidCommandException('--memory-limit must be >= 0')

        assert language_id is not None
        src = self.get_source(source_file) if source_file else self.open_editor(language_id)

        self.judge.submission_id_counter += 1
        self.judge.graded_submissions.append((problem_id, language_id, src, time_limit, memory_limit))
        try:
            self.judge.begin_grading(
                Submission(
                    self.judge.submission_id_counter, problem_id, language_id, src, time_limit, memory_limit, False, {}
                ),
                blocking=True,
                report=print,
            )
        except KeyboardInterrupt:
            self.judge.abort_grading()
