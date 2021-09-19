from typing import Protocol, Union

from dmoj.result import CheckerResult

CheckerOutput = Union[bool, CheckerResult]

class CheckerCallable(Protocol):
    def __call__(
        self,
        process_output: bytes,
        judge_outputz: bytes,
        *,
        submission_source: bytes,
        judge_input: bytes,
        point_value: int,
        case_position: int,
        batch: int,
        submission_language: str,
        binary_data: bool,
        execution_time: float,
        problem_id: str,
        **kwargs
    ) -> CheckerOutput: ...

class Checker(Protocol):
    check: CheckerCallable

bridged: Checker
easy: Checker
floats: Checker
floatsabs: Checker
floatsrel: Checker
identical: Checker
linecount: Checker
linematches: Checker
rstripped: Checker
sorted: Checker
standard: Checker
unordered: Checker
