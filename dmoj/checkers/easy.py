from dmoj.utils.unicode import utf8bytes


def check(process_output, judge_output, **kwargs):
    import re
    from collections import Counter
    process_all = re.sub(br'\s+', '', utf8bytes(process_output))
    judge_all = re.sub(br'\s+', '', utf8bytes(judge_output))
    return Counter(process_all.lower()) == Counter(judge_all.lower())
