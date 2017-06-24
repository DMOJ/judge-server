from __future__ import print_function
import sys

from dmoj.result import CheckerResult

verdict = u"\u2717\u2713"

def error(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def check(process_output, judge_output, point_value,
          feedback=False, match=lambda p, j: p.strip() == j.strip(), **kwargs):

    process_lines = filter(None, process_output.strip().split("\n"))
    judge_lines = filter(None, judge_output.strip().split("\n"))

    # Extraneous output
    if len(process_lines) > len(judge_lines):
        return False

    cases = [verdict[0]] * len(judge_lines)
    count = 0

    # Overload lambda
    if isinstance(match, basestring):
        try:
            match = eval(match)
        except Exception as e:
            error(e.__doc__)
            error(e.message)

    for i, (process_line, judge_line) in enumerate(zip(process_lines, judge_lines)):
        if match(process_line, judge_line):
            cases[i] = verdict[1]
            count += 1

    # Empty answer
    if not judge_lines:
        return True

    return CheckerResult(count == len(judge_lines), point_value * (1.0 * count / len(judge_lines)), ''.join(cases) if feedback else "")
