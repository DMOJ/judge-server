import os

from dmoj.judgeenv import get_problem_root
from dmoj.utils.module import load_module_from_file


class CustomGrader(object):
    def __init__(self, judge, problem, language, source):
        self.judge = judge
        self.mod = load_module_from_file(os.path.join(get_problem_root(problem.id), problem.config['custom_judge']))
        self._grader = self.mod.Grader(judge, problem, language, source)

    def grade(self, case):
        try:
            return self._grader.grade(case)
        except:
            self.judge.internal_error()

    def terminate_grading(self):
        try:
            return self._grader.terminate_grading()
        except:
            self.judge.internal_error()

    def __getattr__(self, item):
        return getattr(self._grader, item)
