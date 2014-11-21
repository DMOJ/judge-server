def check(process_output, judge_output, precision, **kwargs):
    from itertools import izip
    process_lines = filter(None, process_output.split('\n'))
    judge_lines = filter(None, judge_output.split('\n'))
    if len(process_lines) != len(judge_lines):
        return False
    epsilon = 10 ** -int(precision)
    try:
        for process_line, judge_line in izip(process_lines, judge_lines):
            process_floats = map(float, process_line.split())
            judge_floats = map(float, judge_line.split())
            if any(abs(process_float - judge_float) > epsilon and 
                   (abs(judge_float) < epsilon or abs(1.0 - process_float / judge_float) > epsilon)
                     for process_float, judge_float in izip(process_floats, judge_floats)):
                return False
    except:
        return False
    return True
