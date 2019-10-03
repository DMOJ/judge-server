from dmoj.utils.unicode import utf8text


class Result:
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
        'IE': 'red',
    }

    def __init__(self, case):
        self.result_flag = 0
        self.execution_time = 0
        self.wall_clock_time = 0
        self.max_memory = 0
        self.proc_output = ''
        self.feedback = ''
        self.extended_feedback = ''
        self.case = case
        self.points = 0

    def get_main_code(self):
        for flag in ['IE', 'TLE', 'MLE', 'OLE', 'RTE', 'IR', 'WA', 'SC']:
            code = getattr(Result, flag)
            if self.result_flag & code:
                return code
        return Result.AC

    def readable_codes(self):
        execution_verdict = []
        for flag in ['IE', 'TLE', 'MLE', 'OLE', 'RTE', 'IR', 'WA', 'SC']:
            if self.result_flag & getattr(Result, flag):
                execution_verdict.append(flag)
        return execution_verdict or ['AC']

    @property
    def total_points(self):
        return self.case.points

    @property
    def output(self):
        return utf8text(self.proc_output[:self.case.output_prefix_length], 'replace')

    def set_result_flag(self, process):
        if process.returncode > 0:
            self.result_flag |= Result.IR
        if process.returncode is None or process.returncode < 0:
            self.result_flag |= Result.RTE  # Killed by signal
        if process.tle:
            self.result_flag |= Result.TLE
        if process.mle:
            self.result_flag |= Result.MLE


class CheckerResult:
    def __init__(self, passed, points, feedback=None, extended_feedback=None):
        # Make sure we don't kill the site bridge
        assert isinstance(passed, bool)
        assert isinstance(points, int) or isinstance(points, float)
        assert feedback is None or isinstance(feedback, str)
        assert extended_feedback is None or isinstance(extended_feedback, str)

        self.passed = passed
        self.points = points
        self.feedback = feedback
        self.extended_feedback = extended_feedback
