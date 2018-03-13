from dmoj.graders.standard import StandardGrader
from dmoj.result import CheckerResult


class WrongAnswer(BaseException):
    pass


EOF = ''


class Interactor(object):
    def __init__(self, process):
        self.process = process
        self._tokens = None

    def _abbreviate(self, s, n=5):
        if len(s) > n:
            return s[:n] + '...'
        return s

    def read(self):
        ret = self.process.stdout.read()
        if ret == EOF:
            raise IOError('child stream closed')
        return ret

    def readln(self, strip_newline=True):
        ret = self.process.stdout.readline()
        if ret == EOF:
            raise IOError('child stream closed')
        if strip_newline:
            ret = ret.rstrip()
        return ret

    def readtoken(self, delim=None):
        if not self._tokens:
            self._tokens = self.readln()
        try:
            ret, self._tokens = self._tokens.split(delim, 1)
        except ValueError:
            ret = self._tokens
            self._tokens = None
        return ret

    def readint(self, lo=float('-inf'), hi=float('inf'), delim=None):
        token = self.readtoken(delim)
        try:
            ret = int(token)
        except ValueError:
            raise WrongAnswer('expected int, got "%s"' % (self._abbreviate(token)))
        if not lo <= ret <= hi:
            raise WrongAnswer('expected int in range [%.0f, %.0f], got %d' % (lo, hi, ret))
        return ret

    def readfloat(self, lo=float('-inf'), hi=float('inf'), delim=None):
        token = self.readtoken(delim)
        try:
            ret = float(token)
        except ValueError:
            raise WrongAnswer('expected float, got "%s"' % (self._abbreviate(token)))
        if not lo <= ret <= hi:
            raise WrongAnswer('expected float in range [%.2f %.2f], got %.2f' % (lo, hi, ret))
        return ret

    def write(self, val):
        self.process.stdin.write(str(val))
        self.process.stdin.flush()

    def writeln(self, val):
        self.write(str(val) + '\n')

    def close(self):
        for stream in [self.process.stdin, self.process.stdout, self.process.stderr]:
            stream.close()


class InteractiveGrader(StandardGrader):
    def _interact_with_process(self, case, result, input):
        interactor = Interactor(self._current_proc)
        self.check = False
        self.feedback = None
        try:
            self.check = self.interact(case, interactor)
            interactor.close()
        except WrongAnswer as wa:
            self.feedback = str(wa)
        except IOError:
            pass

        self._current_proc.wait()

    def check_result(self, case, result):
        if result.result_flag:
            # This is usually because of a TLE verdict caused by printing stuff after the interactor
            # has issued the AC verdict
            # This results in a TLE verdict getting full points, which should not be the case
            return False
        if not isinstance(self.check, CheckerResult):
            return CheckerResult(self.check, case.points if self.check else 0.0, feedback=self.feedback)
        return self.check

    def interact(self, case, interactor):
        raise NotImplementedError
