def check(process_output, judge_output, **kwargs):
    from judge import TerminateGrading
    epsilon = 10 ** -int(kwargs["precision"])
    for process_line, judge_line in zip(process_output.split('\n'), judge_output.split('\n')):
        try:
            process_floats = map(float, process_line.split())
            judge_floats = map(float, judge_line.split())
        except TerminateGrading:
            raise
        except:
            return False
        for process_float, judge_float in zip(process_floats, judge_floats):
            if abs(process_float - judge_float) > epsilon:
                return False
    return True