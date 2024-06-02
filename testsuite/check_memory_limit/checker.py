from dmoj.checkers import standard
from dmoj.result import Result


def check(process_output: bytes, judge_output: bytes, *, result: Result, **kwargs) -> bool:
    if result.max_memory > 65536:
        return False

    return standard.check(process_output, judge_output, result=result, **kwargs)
