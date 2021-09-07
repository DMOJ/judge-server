import re

from dmoj.contrib.testlib import ContribModule as TestlibContribModule
from dmoj.error import InternalError
from dmoj.result import CheckerResult


class ContribModule(TestlibContribModule):
    name = 'coci'
    repartial = re.compile(br'^partial ((\d+)\/(\d*[1-9]\d*))$', re.M)

    @classmethod
    def get_interactor_args_format_string(cls):
        return '{input_file} {answer_file}'

    @classmethod
    def parse_return_code(cls, proc, executor, point_value, time_limit, memory_limit, feedback, name, stderr):
        if proc.returncode == cls.PARTIAL:
            match = cls.repartial.search(stderr)
            if not match:
                raise InternalError('Invalid stderr for fraction of points: %r' % stderr)
            percentage = int(match.group(2)) / int(match.group(3))
            if not 0.0 <= percentage <= 1.0:
                raise InternalError('Invalid fraction: %s' % match.group(1))
            points = percentage * point_value
            return CheckerResult(True, points, feedback=feedback)
        else:
            return super().parse_return_code(
                proc, executor, point_value, time_limit, memory_limit, feedback, name, stderr
            )
