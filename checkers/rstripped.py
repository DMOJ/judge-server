def check(process_output, judge_output, **kwargs):
    from itertools import izip
    process_lines = process_output.split('\n')
    judge_lines = judge_output.split('\n')
    if 'filter_new_line' in kwargs:
        process_lines = filter(None, process_lines)
        judge_lines = filter(None, judge_lines)
    print process_lines
    print judge_lines
    if len(process_lines) != len(judge_lines):
        print "fail 1"
        return False
    for process_line, judge_line in izip(process_lines, judge_lines):
        if process_line.rstrip() != judge_line.rstrip():
            print "fail 2"
            return False
    return True
