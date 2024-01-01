from typing import Optional, TYPE_CHECKING

from dmoj.cptbox import TracedPopen
from dmoj.executors.base_executor import BaseExecutor
from dmoj.problem import Problem, TestCase
from dmoj.result import Result
from dmoj.utils.unicode import utf8bytes

if TYPE_CHECKING:
    from dmoj.judge import JudgeWorker


class BaseGrader:
    source: bytes
    language: str
    problem: Problem
    judge: 'JudgeWorker'
    binary: BaseExecutor
    _current_proc: Optional[TracedPopen]

    def __init__(self, judge: 'JudgeWorker', problem: Problem, language: str, source: bytes) -> None:
        self.source = utf8bytes(source)
        self.language = language
        self.problem = problem
        self.judge = judge
        self.binary = self._generate_binary()
        self._abort_requested = False
        self._current_proc = None

    def grade(self, case: TestCase) -> Result:
        raise NotImplementedError

    def _generate_binary(self) -> BaseExecutor:
        raise NotImplementedError

    def abort_grading(self) -> None:
        self._abort_requested = True
        if self._current_proc:
            try:
                self._current_proc.kill()
            except OSError:
                pass
