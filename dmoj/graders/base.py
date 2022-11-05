from typing import List, Tuple

from dmoj.config import InvalidInitException
from dmoj.problem import Batch, BatchedTestCase, StandaloneTestCase, TopLevelCase
from dmoj.utils.unicode import utf8bytes


class BaseGrader:
    def __init__(self, judge, problem, language, source):
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

    def grade(self, case):
        raise NotImplementedError

    def _generate_binary(self):
        raise NotImplementedError

    def abort_grading(self):
        self._abort_requested = True
        if self._current_proc:
            try:
                self._current_proc.kill()
            except OSError:
                pass

    def _resolve_testcases(self, cfg) -> List[TopLevelCase]:
        cases: List[TopLevelCase] = []
        for case_config in cfg:
            if 'batched' in case_config.raw_config:
                self._batch_counter += 1
                cases.append(
                    Batch(
                        self._batch_counter,
                        case_config,
                        self.problem,
                        self._resolve_batched_cases(case_config['batched'], self._batch_counter),
                    )
                )
            else:
                self._testcase_counter += 1
                cases.append(StandaloneTestCase(self._testcase_counter, case_config, self.problem))
        return cases

    def _resolve_batched_cases(self, cfg, batch: int) -> List[BatchedTestCase]:
        batched_cases = []
        for case_config in cfg:
            if 'batched' in case_config.raw_config:
                raise InvalidInitException('nested batches')
            self._testcase_counter += 1
            batched_cases.append(BatchedTestCase(self._testcase_counter, batch, case_config, self.problem))
        return batched_cases

    def cases(self) -> Tuple[List[TopLevelCase], List[TopLevelCase]]:
        pretest_test_cases = self.problem.config.pretest_test_cases
        if pretest_test_cases:
            pretest_test_cases = self._resolve_testcases(pretest_test_cases)

            for case in pretest_test_cases:
                # Hack: force short-circuiting behavior
                case.points = 0
        else:
            pretest_test_cases = []

        # Important that this comes after the previous `_resolve_testcases` call, otherwise our underlying `position` values would be all wrong.
        test_cases = self._resolve_testcases(self.problem.config.test_cases)
        return (pretest_test_cases, test_cases)
