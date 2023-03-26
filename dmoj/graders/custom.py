import os

from dmoj.error import InternalError
from dmoj.judgeenv import env, get_problem_root
from dmoj.utils.module import load_module_from_file


class CustomGrader:
    def __init__(self, judge, problem, language, source):
        self.judge = judge
        grader_search_paths = [get_problem_root(problem.id)] + env.get('grader_search_paths', [])
        for search_path in grader_search_paths:
            path = os.path.join(search_path, problem.config['custom_judge'])
            if os.path.isfile(path):
                self.mod = load_module_from_file(path)
                if hasattr(self.mod, 'Grader'):
                    self._grader = self.mod.Grader(judge, problem, language, source)
                break
        else:
            raise InternalError(f'Could not locate grader {problem.config["custom_judge"]}')

    def __getattr__(self, item):
        return getattr(self._grader, item)
