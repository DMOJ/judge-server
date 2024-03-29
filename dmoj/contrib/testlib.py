import re
from typing import TYPE_CHECKING

from dmoj.contrib.default import ContribModule as DefaultContribModule
from dmoj.error import InternalError
from dmoj.executors.base_executor import BaseExecutor
from dmoj.result import CheckerResult
from dmoj.utils.helper_files import parse_helper_file_error

if TYPE_CHECKING:
    from dmoj.cptbox import TracedPopen


class ContribModule(DefaultContribModule):
    AC = 0
    WA = 1
    PE = 2
    IE = 3
    PARTIAL = 7

    name = 'testlib'
    repartial = re.compile(br'^points (\d+)$', re.M)

    @classmethod
    def get_interactor_args_format_string(cls) -> str:
        return '{input_file} {output_file} {answer_file}'

    @classmethod
    def get_validator_args_format_string(cls) -> str:
        return '--group st{batch_no}'

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
        if proc.returncode == cls.AC:
            return CheckerResult(True, point_value, feedback=feedback)
        elif proc.returncode == cls.PARTIAL:
            match = cls.repartial.search(stderr)
            if not match:
                raise InternalError('Invalid stderr for partial points: %r' % stderr)
            points = int(match.group(1))
            if not 0 <= points <= point_value:
                raise InternalError('Invalid partial points: %d' % points)
            return CheckerResult(True, points, feedback=feedback)
        elif proc.returncode == cls.WA:
            return CheckerResult(False, 0, feedback=feedback)
        elif proc.returncode == cls.PE:
            return CheckerResult(False, 0, feedback=feedback or 'Presentation Error')
        elif proc.returncode == cls.IE:
            raise InternalError('%s failed assertion with message %s' % (name, feedback))
        else:
            parse_helper_file_error(proc, executor, name, stderr, time_limit, memory_limit)
