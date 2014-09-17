def check(process_output, judge_output, data):
    from judge import TerminateGrading
    epsilon = 10 ** -int(data["precision"])
    process_lines = filter(None, process_output.split('\n'))
    judge_lines = filter(None, judge_output.split('\n'))
    if len(process_lines) != len(judge_lines):
        return False
    for process_line, judge_line in zip(process_lines, judge_lines):
        try:
            process_floats = map(float, process_line.split())
            judge_floats = map(float, judge_line.split())
        except TerminateGrading:
            raise
        except:
            return False
        for process_float, judge_float in zip(process_floats, judge_floats):
            if abs(process_float - judge_float) > epsilon and (abs(judge_float) < epsilon or abs(1.0 - process_float / judge_float) > epsilon):
                return False
    return True
