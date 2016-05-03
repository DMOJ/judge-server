import os

from dmoj.judgeenv import get_problem_root
from dmoj.utils.module import load_module_from_file


class CustomGrader(object):
    def __init__(self, judge, problem, language, source):
        mod = load_module_from_file(os.path.join(get_problem_root(problem.id), problem.config['custom_judge']))
        self.custom_judge = mod.Grader(judge, problem, language, source)

    def grade(self, case):
        return self.custom_judge.grade(case)

    def terminate_grading(self):
        return self.custom_judge.terminate_grading()
