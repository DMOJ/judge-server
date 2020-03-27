from re import split as resplit

from dmoj.error import InternalError
from dmoj.utils.unicode import utf8bytes


def verify_absolute(process_float: float, judge_float: float, epsilon: float) -> bool:
    # Since process_float can be NaN, this is NOT equivalent to
    # (process_float - judge_float) > epsilon;  the code below will always
    # reject NaN, even if judge_float is NaN
    return abs(process_float - judge_float) <= epsilon


def verify_relative(process_float: float, judge_float: float, epsilon: float) -> bool:
    p1 = min(judge_float * (1 - epsilon), judge_float * (1 + epsilon))
    p2 = max(judge_float * (1 - epsilon), judge_float * (1 + epsilon))
    # Since process_float can be NaN, this is NOT equivalent to
    # (process_float < p1 or process_float > p2)
    return p1 <= process_float <= p2


def verify_default(process_float: float, judge_float: float, epsilon: float) -> bool:
    # process_float can be NaN
    # in this case, we reject NaN as a possible answer, even if judge_float is NaN
    return (
        abs(process_float - judge_float) <= epsilon
        or abs(judge_float) >= epsilon
        and abs(1.0 - process_float / judge_float) <= epsilon
    )


def check(
    process_output: bytes, judge_output: bytes, precision: int = 6, error_mode: str = 'default', **kwargs
) -> bool:
    # Discount empty lines
    process_lines = list(filter(None, resplit(b'[\r\n]', utf8bytes(process_output))))
    judge_lines = list(filter(None, resplit(b'[\r\n]', utf8bytes(judge_output))))

    if len(process_lines) != len(judge_lines):
        return False

    verify_float = {'absolute': verify_absolute, 'relative': verify_relative, 'default': verify_default}.get(error_mode)

    if not verify_float:
        raise InternalError('invalid `error_mode` value')

    epsilon = 10 ** -int(precision)

    try:
        for process_line, judge_line in zip(process_lines, judge_lines):
            process_tokens = process_line.split()
            judge_tokens = judge_line.split()

            if len(process_tokens) != len(judge_tokens):
                return False

            for process_token, judge_token in zip(process_tokens, judge_tokens):
                # Allow mixed tokens, for lines like "abc 0.68 def 0.70"
                try:
                    judge_float = float(judge_token)
                except ValueError:
                    # If it's not a float the token must match exactly
                    if process_token != judge_token:
                        return False
                else:
                    process_float = float(process_token)

                    if not verify_float(process_float, judge_float, epsilon):
                        return False
    except Exception:
        return False
    return True
