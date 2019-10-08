from operator import itemgetter

from dmoj import judgeenv
from dmoj.commands.base_command import Command
from dmoj.error import InvalidCommandException
from dmoj.executors import executors


class SubmitCommand(Command):
    name = 'submit'
    help = 'Grades a submission.'

    def _populate_parser(self):
        self.arg_parser.add_argument('problem_id', help='id of problem to grade')
        self.arg_parser.add_argument('language_id', nargs='?', default=None,
                                     help='id of the language to grade in (e.g., PY2)')
        self.arg_parser.add_argument('source_file', nargs='?', default=None,
                                     help='path to submission source (optional)')
        self.arg_parser.add_argument('-tl', '--time-limit', type=float, help='time limit for grading, in seconds',
                                     default=2.0, metavar='<time limit>')
        self.arg_parser.add_argument('-ml', '--memory-limit', type=int, help='memory limit for grading, in kilobytes',
                                     default=65536, metavar='<memory limit>')

    def execute(self, line):
        args = self.arg_parser.parse_args(line)

        problem_id = args.problem_id
        language_id = args.language_id
        time_limit = args.time_limit
        memory_limit = args.memory_limit
        source_file = args.source_file

        if language_id not in executors:
            source_file = language_id
            language_id = None  # source file / language id optional

        if problem_id not in map(itemgetter(0), judgeenv.get_supported_problems()):
            raise InvalidCommandException("unknown problem '%s'" % problem_id)
        elif not language_id:
            if source_file:
                filename, dot, ext = source_file.partition('.')
                if not ext:
                    raise InvalidCommandException('invalid file name')
                else:
                    # TODO: this should be a proper lookup elsewhere
                    ext = ext.upper()
                    language_id = {
                        'PY': 'PY2',
                        'CPP': 'CPP11',
                        'JAVA': 'JAVA8',
                    }.get(ext, ext)
            else:
                raise InvalidCommandException("no language is selected")
        elif language_id not in executors:
            raise InvalidCommandException("unknown language '%s'" % language_id)
        elif time_limit <= 0:
            raise InvalidCommandException('--time-limit must be >= 0')
        elif memory_limit <= 0:
            raise InvalidCommandException('--memory-limit must be >= 0')

        src = self.get_source(source_file) if source_file else self.open_editor(language_id)

        self.judge.submission_id_counter += 1
        self.judge.graded_submissions.append((problem_id, language_id, src, time_limit, memory_limit))
        self.judge.begin_grading(self.judge.submission_id_counter, problem_id, language_id, src, time_limit,
                                 memory_limit, False, False, blocking=True)
