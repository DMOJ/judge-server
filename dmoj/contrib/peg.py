from dmoj.contrib.default import ContribModule as DefaultContribModule
from dmoj.result import CheckerResult
from dmoj.utils.helper_files import parse_helper_file_error


class ContribModule(DefaultContribModule):
    name = 'peg'

    @classmethod
    def get_checker_args_format_string(cls):
        return '{answer_file} {output_file} {input_file}'

    @classmethod
    def parse_return_code(cls, proc, executor, point_value, time_limit, memory_limit, feedback, name, stderr):
        if proc.returncode in (cls.AC, cls.WA):
            # PEG allows for a ratio of floating points, and can give partials for AC or WA
            # Scanning for floating points with a regex is impractical, so we loop all lines
            feedback_lines = feedback.split('\n')
            for line1, line2 in zip(feedback_lines, feedback_lines[1:]):
                try:
                    percentage = float(line1) / float(line2)
                except (ValueError, ZeroDivisionError):
                    pass
                else:
                    if percentage > 0:
                        # We like to return _AC for partials
                        return CheckerResult(True, point_value * percentage)
            return proc.returncode == cls.AC
        else:
            parse_helper_file_error(proc, executor, name, stderr, time_limit, memory_limit)
