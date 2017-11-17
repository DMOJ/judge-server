from ._checker import standard


def check(process_output, judge_output, _checker=standard, **kwargs):
    return _checker(judge_output, process_output)


del standard
