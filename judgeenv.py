import json
import os

__all__ = ['env']

with open(os.path.join(os.path.dirname(__file__), 'data', 'judge', 'judge.json')) as init_file:
    env = json.load(init_file)
