from typing import TYPE_CHECKING

from dmoj.contrib.base import BaseContribModule
from dmoj.executors.base_executor import BaseExecutor
from dmoj.result import CheckerResult
from dmoj.utils.helper_files import parse_helper_file_error

if TYPE_CHECKING:
    from dmoj.cptbox import TracedPopen


class ContribModule(BaseContribModule):
    name = 'default'

    @classmethod
    def get_checker_args_format_string(cls) -> str:
        return '{input_file} {output_file} {answer_file}'

    @classmethod
    def get_interactor_args_format_string(cls) -> str:
        return '{input_file} {answer_file}'

    @classmethod
    def get_validator_args_format_string(cls) -> str:
        return '{batch_no} {case_no}'

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
        elif proc.returncode == cls.WA:
            return CheckerResult(False, 0, feedback=feedback)
        else:
            parse_helper_file_error(proc, executor, name, stderr, time_limit, memory_limit)
