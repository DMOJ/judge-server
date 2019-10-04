from dmoj.checkers.floats import check as floats_check


def check(process_output: bytes, judge_output: bytes, **kwargs) -> bool:
    return floats_check(process_output, judge_output, error_mode='relative', **kwargs)
