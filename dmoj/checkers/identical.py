from dmoj.checkers._checker import standard
from dmoj.result import CheckerResult
from dmoj.utils.unicode import utf8bytes

def check(process_output, judge_output, pe_allowed=False, **kwargs):
    if judge_output == process_output:
        return True
    feedback = None
    if pe_allowed and standard(utf8bytes(judge_output), utf8bytes(process_output)):
        # in the event the standard checker would have passed the problem, raise a presentation error
        feedback = "Presentation Error"
    return CheckerResult(False, 0, feedback=feedback)
