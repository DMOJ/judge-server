def check(process_output, judge_output, **kwargs):
    import re
    from collections import Counter
    process_all = re.sub(r'\s+', '', process_output)
    judge_all = re.sub(r'\s+', '', judge_output)
    return Counter(process_all) == Counter(judge_all)
