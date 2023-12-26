import re
from typing import TYPE_CHECKING

from dmoj.contrib.testlib import ContribModule as TestlibContribModule
from dmoj.error import InternalError
from dmoj.executors.base_executor import BaseExecutor
from dmoj.result import CheckerResult
from dmoj.utils.unicode import utf8text

if TYPE_CHECKING:
    from dmoj.cptbox import TracedPopen


class ContribModule(TestlibContribModule):
    name = 'coci'
    repartial = re.compile(br'^partial ((\d+)\/(\d*[1-9]\d*))$', re.M)

    @classmethod
    def get_interactor_args_format_string(cls) -> str:
        return '{input_file} {answer_file}'

    @classmethod
    def get_validator_args_format_string(cls) -> str:
        raise NotImplementedError

    @classmethod
    def parse_return_code(
        cls,
        proc: 'TracedPopen',
        executor: BaseExecutor,
        point_value: float,
        time_limit: float,
        memory_limit: int,
        feedback: str,
        name: str,
        stderr: bytes,
    ):
        if proc.returncode == cls.PARTIAL:
            match = cls.repartial.search(stderr)
            if not match:
                raise InternalError('Invalid stderr for fraction of points: %r' % stderr)
            percentage = int(match.group(2)) / int(match.group(3))
            if not 0.0 <= percentage <= 1.0:
                raise InternalError(f'Invalid fraction: {utf8text(match.group(1))}')
            points = percentage * point_value
            return CheckerResult(True, points, feedback=feedback)
        else:
            return super().parse_return_code(
                proc, executor, point_value, time_limit, memory_limit, feedback, name, stderr
            )
