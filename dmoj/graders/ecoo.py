from dmoj.graders.standard import StandardGrader
from dmoj.result import CheckerResult
from dmoj.utils.unicode import utf8text


class ECOOGrader(StandardGrader):
    def check_result(self, case, result):
        check = super().check_result(case, result)
        if not isinstance(check, CheckerResult):
            check = CheckerResult(check, case.points if check else 0.0)
        if not check.passed:
            check.extended_feedback = utf8text(case.input_data())
        return check

    def cases(self):
        cfg = self.problem.config['pretest_test_cases' if self.is_pretested else 'test_cases']
        if self.meta.contest_no is not None:
            return self._resolve_testcases(cfg.get(self.meta.attempt_no, 'default'))
        else:
            return self._resolve_testcases(cfg['default'])
