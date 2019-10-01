from dmoj.checkers.floats import check as floats_check


def check(process_output: str, judge_output: str, **kwargs) -> bool:
    return floats_check(process_output, judge_output, error_mode='relative', **kwargs)
