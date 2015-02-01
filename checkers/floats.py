def check(process_output, judge_output, precision, **kwargs):
    from itertools import izip
    process_lines = filter(None, process_output.split('\n'))
    judge_lines = filter(None, judge_output.split('\n'))
    if len(process_lines) != len(judge_lines):
        return False
    epsilon = 10 ** -int(precision)
    try:
        for process_line, judge_line in izip(process_lines, judge_lines):
            process_floats = process_line.split()
            judge_floats = judge_line.split()
            for process_token, judge_token in izip(process_floats, judge_floats):
                try:
                    judge_float = float(judge_token)
                except:
                    if process_token != judge_token:
                        return False
                else:
                    process_float = float(process_token)
                    if abs(process_float - judge_float) > epsilon and \
                           (abs(judge_float) < epsilon or abs(1.0 - process_float / judge_float) > epsilon):
                        return False
    except:
        return False
    return True
