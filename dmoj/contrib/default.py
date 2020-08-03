from dmoj.result import CheckerResult
from dmoj.utils.helper_files import parse_helper_file_error


class ContribModule:
    AC = 0
    WA = 1

    name = 'default'

    @classmethod
    def get_checker_args_format_string(cls):
        return '{input_file} {output_file} {answer_file}'

    @classmethod
    def get_interactor_args_format_string(cls):
        return '{input_file} {answer_file}'

    @classmethod
    def parse_return_code(cls, proc, executor, point_value, time_limit, memory_limit, feedback, name, stderr):
        if proc.returncode == cls.AC:
            return CheckerResult(True, point_value, feedback=feedback)
        elif proc.returncode == cls.WA:
            return CheckerResult(False, 0, feedback=feedback)
        else:
            parse_helper_file_error(proc, executor, name, stderr, time_limit, memory_limit)
