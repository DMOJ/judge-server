def check(process_output, judge_output, **kwargs):
    from six.moves import zip
    from string import split
    process_lines = list(filter(None, process_output.split('\n')))
    judge_lines = list(filter(None, judge_output.split('\n')))
    if len(process_lines) != len(judge_lines):
        return False
    process_lines = map(split, process_lines)
    judge_lines = map(split, judge_lines)
    process_lines.sort()
    judge_lines.sort()
    for process_line, judge_line in zip(process_lines, judge_lines):
        if process_line != judge_line:
            return False
    return True
