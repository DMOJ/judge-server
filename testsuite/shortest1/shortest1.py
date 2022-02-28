from dmoj.graders.standard import StandardGrader
from dmoj.result import Result, CheckerResult


class Grader(StandardGrader):
    def check_result(self, case, result):
        passed = bool(result.result_flag & Result.TLE)
        result.result_flag &= ~Result.TLE & ~Result.RTE & ~Result.IR
        return CheckerResult(passed, min((9. / len(self.source)) ** 5 * case.points, case.points) if passed else 0)

    def _interact_with_process(self, case, result):
        process = self._current_proc
        for handle in [process.stdin, process.stdout, process.stderr]:
            if handle:
                handle.close()
        process.wait()
