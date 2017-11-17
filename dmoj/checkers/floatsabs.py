from six.moves import zip, filter


def check(process_output, judge_output, precision, **kwargs):
    process_lines = list(filter(None, process_output.split(b'\n')))
    judge_lines = list(filter(None, judge_output.split(b'\n')))

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
                    if abs(process_float - judge_float) > epsilon:
                        return False
    except:
        return False
    return True
