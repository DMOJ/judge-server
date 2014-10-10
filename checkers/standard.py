def check(process_output, judge_output, **kwargs):
    process_lines = filter(None, process_output.split('\n'))
    judge_lines = filter(None, judge_output.split('\n'))
    if len(process_lines) != len(judge_lines):
        return False
    for process_line, judge_line in zip(process_lines, judge_lines):
        process_line = process_line.split()
        judge_line = judge_line.split()
        if process_line != judge_line:
            return False
    return True
