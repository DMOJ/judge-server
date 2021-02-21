#! -*- encoding: utf-8 -*-

def check(process_output, judge_output, judge_input, point_value, submission_source, **kwargs):
    from dmoj.result import CheckerResult

    if not process_output:
        return CheckerResult(False, 0)
    return CheckerResult(True, point_value, '正しい出力なのです')
