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
    COLORS_BYID = {
        'AC': 'green',
        'WA': 'red',
        'RTE': 'yellow',
        'TLE': 'white',
        'MLE': 'yellow',
        'IR': 'yellow',
        'SC': 'magenta',
        'OLE': 'yellow',
        'IE': 'red'
    }

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
        for flag in ['IE', 'TLE', 'MLE', 'OLE', 'RTE', 'IR', 'WA', 'SC']:
            if self.result_flag & getattr(Result, flag):
                execution_verdict.append(flag)
        return execution_verdict or ['AC']


class CheckerResult(object):
    def __init__(self, passed, points, feedback=None):
        self.passed = passed
        self.points = points
        self.feedback = feedback
