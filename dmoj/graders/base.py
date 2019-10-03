from dmoj.config import ConfigNode
from dmoj.problem import BatchedTestCase, TestCase
from dmoj.utils.unicode import utf8bytes


class BaseGrader:
    def __init__(self, judge, problem, language, source, meta):
        self.source = utf8bytes(source)
        self.language = language
        self.problem = problem
        self.judge = judge
        self.meta = ConfigNode(meta)
        self.binary = self._generate_binary()
        self.is_pretested = self.meta.pretests_only and 'pretest_test_cases' in self.problem.config
        self._terminate_grading = False
        self._current_proc = None
        self._batch_counter = 0
        self._testcase_counter = 0

    def grade(self, case):
        raise NotImplementedError

    def _generate_binary(self):
        raise NotImplementedError

    def terminate_grading(self):
        self._terminate_grading = True
        if self._current_proc:
            try:
                self._current_proc.kill()
            except OSError:
                pass

    def _resolve_testcases(self, cfg, batch_no=0):
        cases = []
        for case_config in cfg:
            if 'batched' in case_config.raw_config:
                self._batch_counter += 1
                cases.append(BatchedTestCase(self._batch_counter, case_config, self.problem,
                                             self._resolve_testcases(case_config['batched'], self._batch_counter)))
            else:
                cases.append(TestCase(self._testcase_counter, batch_no, case_config, self.problem))
                self._testcase_counter += 1
        return cases

    def cases(self):
        key = 'pretest_test_cases' if self.is_pretested else 'test_cases'
        return self._resolve_testcases(self.problem.config[key])
