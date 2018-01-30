from re import split as resplit

from six.moves import zip, filter

from dmoj.utils.unicode import utf8bytes


def check(process_output, judge_output, precision, **kwargs):
    # Discount empty lines
    process_lines = list(filter(None, resplit(b'[\r\n]', utf8bytes(process_output))))
    judge_lines = list(filter(None, resplit(b'[\r\n]', utf8bytes(judge_output))))

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
                # Allow mixed tokens, for lines like "abc 0.68 def 0.70"
                try:
                    judge_float = float(judge_token)
                except:
                    # If it's not a float the token must match exactly
                    if process_token != judge_token:
                        return False
                else:
                    process_float = float(process_token)
                    # process_float can be nan
                    # in this case, we reject nan as a possible answer, even if judge_float is nan
                    if not abs(process_float - judge_float) <= epsilon and \
                            (not abs(judge_float) >= epsilon or not abs(1.0 - process_float / judge_float) <= epsilon):
                        return False
    except:
        return False
    return True
