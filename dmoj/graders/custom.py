import os

from dmoj.judgeenv import get_problem_root
from dmoj.utils.module import load_module_from_file


class CustomGrader:
    def __init__(self, judge, problem, language, source):
        self.judge = judge
        self.mod = load_module_from_file(os.path.join(get_problem_root(problem.id), problem.config['custom_judge']))
        self._grader = self.mod.Grader(judge, problem, language, source)

    def __getattr__(self, item):
        return getattr(self._grader, item)
