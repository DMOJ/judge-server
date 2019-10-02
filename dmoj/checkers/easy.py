import re
from collections import Counter

from dmoj.utils.unicode import utf8bytes


def check(process_output: bytes, judge_output: bytes, Counter=Counter, regex=re.compile(br'\s+'), **kwargs) -> bool:
    process_all = regex.sub(b'', utf8bytes(process_output))
    judge_all = regex.sub(b'', utf8bytes(judge_output))
    return Counter(process_all.lower()) == Counter(judge_all.lower())
