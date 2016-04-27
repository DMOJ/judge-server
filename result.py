class Result(object):
    AC = 0
    WA = 1 << 0
    RTE = 1 << 1
    TLE = 1 << 2
    MLE = 1 << 3
    IR = 1 << 4
    SC = 1 << 5
    OLE = 1 << 6
    IE = 1 << 30

    def __init__(self):
        self.result_flag = 0
        self.execution_time = 0
        self.r_execution_time = 0
        self.max_memory = 0
        self.proc_output = ''
        self.feedback = ''
        self.case = None
        self.points = 0

    def readable_codes(self):
        execution_verdict = []
        for flag in ['IR', 'WA', 'RTE', 'TLE', 'MLE', 'SC', 'IE']:
            if self.result_flag & getattr(Result, flag):
                execution_verdict.append(flag)
        return execution_verdict or ['AC']