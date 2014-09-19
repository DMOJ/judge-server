def check(process_output, judge_output, data):
    import string
    process_lines = filter(None, process_output.split('\n'))
    judge_lines = filter(None, judge_output.split('\n'))
    if len(process_lines) != len(judge_lines):
        return False
    process_lines = map(string.split, process_lines)
    judge_lines = map(string.split, judge_lines)
    process_lines.sort()
    judge_lines.sort()
    for process_line, judge_line in zip(process_lines, judge_lines):
        if process_line != judge_line:
            return False
    return True
