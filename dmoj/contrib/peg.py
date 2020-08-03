import re

from dmoj.contrib.default import ContribModule as DefaultContribModule
from dmoj.result import CheckerResult
from dmoj.utils.helper_files import parse_helper_file_error


class ContribModule(DefaultContribModule):
    name = 'peg'
    repartial = re.compile(r'^(\d+)\n(\d+)$', re.M)

    @classmethod
    def get_checker_args_string(cls):
        return '{output} {answer} {input}'

    @classmethod
    def parse_return_code(cls, proc, executor, point_value, time_limit, memory_limit, feedback, name, stderr):
        if proc.returncode == cls.AC:
            return True
        elif proc.returncode == cls.WA:
            # So for some reason, PEG doesn't have a separate return code for partials
            match = cls.repartial.search(feedback)
            if match:
                # We like to return _AC for partials, vs PEG and WA
                percentage = int(match.group(1)) / int(match.group(2))
                if percentage:
                    return CheckerResult(True, point_value * percentage)
            return False
        else:
            parse_helper_file_error(proc, executor, name, stderr, time_limit, memory_limit)
