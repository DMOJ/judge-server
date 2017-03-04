def check(process_output, judge_output, **kwargs):
    process_tokens = process_output.split()
    judge_tokens = judge_output.split()
    return len(process_tokens) == len(judge_tokens) and sorted(process_tokens) == sorted(judge_tokens)
