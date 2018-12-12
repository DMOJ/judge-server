from dmoj.checkers.floats import check as floats_check


def check(process_output, judge_output, **kwargs):
    return floats_check(process_output, judge_output, error_mode='absolute', **kwargs)
