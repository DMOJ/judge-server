import os
import traceback

from dmoj.judgeenv import get_problem_root
from dmoj.utils.module import load_module_from_file


class CustomGrader(object):
    def __init__(self, judge, problem, language, source):
        self.judge = judge
        mod = load_module_from_file(os.path.join(get_problem_root(problem.id), problem.config['custom_judge']))
        self.custom_judge = mod.Grader(judge, problem, language, source)

    def grade(self, case):
        try:
            return self.custom_judge.grade(case)
        except:
            self.judge.internal_error()

    def terminate_grading(self):
        try:
            return self.custom_judge.terminate_grading()
        except:
            self.judge.internal_error()
