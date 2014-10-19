import json
import os

__all__ = ['env']

_judge_dirs = []

with open(os.path.join(os.path.dirname(__file__), 'data', 'judge', 'judge.json')) as init_file:
    env = json.load(init_file)
    dirs = env.get('problem_storage_root', os.path.join('data', 'problems'))
    if type(dirs) == list:
        _judge_dirs = list(dirs)
    else:
        _judge_dirs = [dirs]


def get_problem_root(pid):
    for dir in _judge_dirs:
        path = os.path.join(dir, pid)
        if os.path.exists(path):
            return path
    return None
