from re import split as resplit

from six.moves import zip, filter

from dmoj.utils.unicode import utf8bytes


def check(process_output, judge_output, precision, **kwargs):
    process_lines = list(filter(None, resplit(b'[\r\n]', utf8bytes(process_output))))
    judge_lines = list(filter(None, resplit(b'[\r\n]', judge_output)))

    if len(process_lines) != len(judge_lines):
        return False

    epsilon = 10 ** -int(precision)

    try:
        for process_line, judge_line in zip(process_lines, judge_lines):
            process_tokens = process_line.split()
            judge_tokens = judge_line.split()

            if len(process_tokens) != len(judge_tokens):
                return False

            for process_token, judge_token in zip(process_tokens, judge_tokens):
                try:
                    judge_float = float(judge_token)
                except:
                    if process_token != judge_token:
                        return False
                else:
                    process_float = float(process_token)
                    # since process_float can be nan, this is NOT equivalent to (process_float - judge_float) > epsilon
                    # the code below will always reject nan, even if judge_float is nan
                    if not abs(process_float - judge_float) <= epsilon:
                        return False
    except:
        return False
    return True
