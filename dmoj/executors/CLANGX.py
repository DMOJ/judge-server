from dmoj.executors.CPP11 import Executor as CPP11Executor
from dmoj.judgeenv import env


class Executor(CPP11Executor):
    command = env['runtime'].get('clang++')
    name = 'CLANG++'
