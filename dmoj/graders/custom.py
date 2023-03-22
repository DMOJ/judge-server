from pathlib import Path

from dmoj.error import InternalError
from dmoj.judgeenv import get_problem_root
from dmoj.utils.module import load_module_from_file


class CustomGrader:
    def __init__(self, judge, problem, language, source):
        self.judge = judge
        custom_judge = problem.config['custom_judge']
        filename = Path(get_problem_root(problem.id), custom_judge)
        if not filename.exists():
            filename = Path(__file__).parent / custom_judge
        if not filename.exists():
            raise InternalError(f'Could not load custom judge {custom_judge}')

        self.mod = load_module_from_file(filename)
        self._grader = self.mod.Grader(judge, problem, language, source)

    def __getattr__(self, item):
        return getattr(self._grader, item)
