import json
import os

__all__ = ['env', 'get_problem_root', 'get_problem_roots']

_judge_dirs = ()
_root = os.path.dirname(__file__)

with open(os.path.join(_root, 'data', 'judge', 'judge.json')) as init_file:
    env = json.load(init_file)
    dirs = env.get('problem_storage_root', os.path.join('data', 'problems'))
    if isinstance(dirs, list):
        _judge_dirs = tuple(os.path.normpath(os.path.join(_root, dir)) for dir in dirs)
    else:
        _judge_dirs = os.path.normpath(os.path.join(_root, dirs)),


def get_problem_root(pid):
    for dir in _judge_dirs:
        path = os.path.join(dir, pid)
        if os.path.exists(path):
            return path
    return None


def get_problem_roots():
    return _judge_dirs