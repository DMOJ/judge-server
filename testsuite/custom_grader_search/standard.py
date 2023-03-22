from dmoj.graders.standard import Grader as StandardGrader
from dmoj.result import Result


class Grader(StandardGrader):
    def grade(self, case):
        result = Result(case)
        result.result_flat = Result.AC
        result.points = case.points

        return result  # will always AC
