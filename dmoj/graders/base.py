from dmoj.problem import BatchedTestCase, TestCase
from dmoj.utils.unicode import utf8bytes


class BaseGrader:
    def __init__(self, judge, problem, language, source):
        self.source = utf8bytes(source)
        self.language = language
        self.problem = problem
        self.judge = judge
        self.binary = self._generate_binary()
        self.is_pretested = self.problem.meta.pretests_only and 'pretest_test_cases' in self.problem.config
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

    def _resolve_testcases(self, cfg, batch_no=0, kind=TestCase.KIND_NORMAL):
        cases = []
        for case_config in cfg:
            # Hack for backwards-compatibility: if points are set to 0, this is a
            # pretest regardless of whatever [kind] was specified to be.
            real_kind = kind if case_config.points else TestCase.KIND_PRETEST
            if 'batched' in case_config.raw_config:
                self._batch_counter += 1
                cases.append(BatchedTestCase(self._batch_counter, real_kind, case_config, self.problem,
                                             self._resolve_testcases(case_config['batched'], self._batch_counter,
                                                                     kind=real_kind)))
            else:
                cases.append(TestCase(self._testcase_counter, batch_no, real_kind, case_config, self.problem))
                self._testcase_counter += 1
        return cases

    def cases(self):
        if 'sample_test_cases' in self.problem.config:
            samples = self._resolve_testcases(self.problem.config.sample_test_cases, kind=TestCase.KIND_SAMPLE)
        else:
            samples = []

        key = 'pretest_test_cases' if self.is_pretested else 'test_cases'
        kind = TestCase.KIND_PRETEST if self.is_pretested else TestCase.KIND_NORMAL
        return samples + self._resolve_testcases(self.problem.config[key], kind=kind)
