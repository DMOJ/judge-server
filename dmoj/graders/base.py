from typing import List, Optional, TYPE_CHECKING

from dmoj.cptbox import TracedPopen
from dmoj.executors.base_executor import BaseExecutor
from dmoj.problem import BaseTestCase, BatchedTestCase, Problem, TestCase
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
    is_pretested: bool
    _current_proc: Optional[TracedPopen]

    def __init__(self, judge: 'JudgeWorker', problem: Problem, language: str, source: bytes) -> None:
        self.source = utf8bytes(source)
        self.language = language
        self.problem = problem
        self.judge = judge
        self.binary = self._generate_binary()
        self.run_pretests_only = self.problem.meta.pretests_only
        self._abort_requested = False
        self._current_proc = None
        self._batch_counter = 0
        self._testcase_counter = 0

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

    def _resolve_testcases(self, cfg, batch_no=0) -> List[BaseTestCase]:
        cases: List[BaseTestCase] = []
        for case_config in cfg:
            if 'batched' in case_config.raw_config:
                self._batch_counter += 1
                cases.append(
                    BatchedTestCase(
                        self._batch_counter,
                        case_config,
                        self.problem,
                        self._resolve_testcases(case_config['batched'], self._batch_counter),
                    )
                )
            else:
                cases.append(TestCase(self._testcase_counter, batch_no, case_config, self.problem))
                self._testcase_counter += 1
        return cases

    def cases(self) -> List[BaseTestCase]:
        pretest_test_cases = self.problem.config.pretest_test_cases
        if self.run_pretests_only and pretest_test_cases:
            return self._resolve_testcases(pretest_test_cases)

        test_cases = self._resolve_testcases(self.problem.config.test_cases)
        if pretest_test_cases:
            pretest_test_cases = self._resolve_testcases(pretest_test_cases)

            # Hack: force short-circuiting behavior
            for case in pretest_test_cases:
                case.points = 0

            test_cases = pretest_test_cases + test_cases

        return test_cases
