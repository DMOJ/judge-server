def check(process_output, judge_output, **kwargs):
    from itertools import izip
    process_lines = filter(None, process_output.split('\n'))
    judge_lines = filter(None, judge_output.split('\n'))
    if len(process_lines) != len(judge_lines):
        return False
    for process_line, judge_line in izip(process_lines, judge_lines):
        if process_line.split() != judge_line.split():
            return False
    return True

try:
    from ._checker import standard
except ImportError as e:
    import sys
    print>> sys.stderr, 'Compile _checker for optimal performance'
else:
    def check(process_output, judge_output, _checker=standard, **kwargs):
        return _checker(judge_output, process_output)
    del standard
