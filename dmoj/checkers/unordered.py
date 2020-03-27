import warnings

from dmoj.checkers.sorted import check as sorted_check


def check(process_output: bytes, judge_output: bytes, **kwargs) -> bool:
    warnings.warn(
        '`unordered` checker is deprecated, use `sorted` with `split_on` parameter instead', DeprecationWarning
    )
    return sorted_check(process_output, judge_output, split_on='whitespace')
