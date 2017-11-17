from six.moves import zip, filter


def check(process_output, judge_output, **kwargs):
    process_lines = process_output.split(b'\n')
    judge_lines = judge_output.split(b'\n')

    if 'filter_new_line' in kwargs:
        process_lines = list(filter(None, process_lines))
        judge_lines = list(filter(None, judge_lines))

    if len(process_lines) != len(judge_lines):
        return False

    for process_line, judge_line in zip(process_lines, judge_lines):
        if process_line.rstrip() != judge_line.rstrip():
            return False

    return True
