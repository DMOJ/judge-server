from typing import Any, AnyStr, Optional

from dmoj.checkers import CheckerOutput
from dmoj.cptbox import TracedPopen
from dmoj.graders.standard import StandardGrader
from dmoj.problem import TestCase
from dmoj.result import CheckerResult, Result
from dmoj.utils.unicode import utf8bytes, utf8text


class WrongAnswer(BaseException):
    pass


EOF = b''
MAX_NUMBER_DIGITS = 10000


class Interactor:
    _tokens: Optional[bytes]

    def __init__(self, process: TracedPopen) -> None:
        self.process = process
        self._tokens = None

    def _abbreviate(self, s: AnyStr, n: int = 5) -> str:
        text = utf8text(s)
        if len(text) > n:
            return text[:n] + '...'
        return text

    def read(self) -> bytes:
        assert self.process.stdout is not None
        ret = self.process.stdout.read()
        if ret == EOF:
            raise IOError('child stream closed')
        return ret

    def readln(self, strip_newline: bool = True) -> bytes:
        assert self.process.stdout is not None
        ret = self.process.stdout.readline()
        if ret == EOF:
            raise IOError('child stream closed')
        if strip_newline:
            ret = ret.rstrip()
        return ret

    def readtoken(self, delim: Optional[bytes] = None) -> bytes:
        if not self._tokens:
            self._tokens = self.readln()
        try:
            ret, self._tokens = self._tokens.split(delim, 1)
        except ValueError:
            ret = self._tokens
            self._tokens = None
        return ret

    def readint(self, lo: float = float('-inf'), hi: float = float('inf'), delim: Optional[bytes] = None) -> int:
        token = self.readtoken(delim)

        if len(token) > MAX_NUMBER_DIGITS:
            raise WrongAnswer('integer is too long')

        try:
            ret = int(token)
        except ValueError:
            raise WrongAnswer('expected int, got "%s"' % (self._abbreviate(token)))

        if not lo <= ret <= hi:
            raise WrongAnswer('expected int in range [%.0f, %.0f], got %d' % (lo, hi, ret))

        return ret

    def readfloat(self, lo: float = float('-inf'), hi: float = float('inf'), delim: Optional[bytes] = None) -> float:
        token = self.readtoken(delim)

        if len(token) > MAX_NUMBER_DIGITS:
            raise WrongAnswer('float is too long')

        try:
            ret = float(token)
        except ValueError:
            raise WrongAnswer('expected float, got "%s"' % (self._abbreviate(token)))

        if not lo <= ret <= hi:
            raise WrongAnswer('expected float in range [%.2f %.2f], got %.2f' % (lo, hi, ret))

        return ret

    def write(self, val: Any) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(utf8bytes(str(val)))
        self.process.stdin.flush()

    def writeln(self, val: Any) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(utf8bytes(str(val) + '\n'))
        self.process.stdin.flush()

    def close(self) -> None:
        assert self.process.stdin is not None
        self.process.stdin.close()


class InteractiveGrader(StandardGrader):
    check: CheckerOutput

    def _launch_process(self, case, input_file=None):
        super()._launch_process(case, input_file=None)

    def _interact_with_process(self, case: TestCase, result: Result) -> bytes:
        assert self._current_proc is not None
        assert self._current_proc.stderr is not None

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
        return self._current_proc.stderr.read()

    def check_result(self, case: TestCase, result: Result) -> CheckerOutput:
        if result.result_flag:
            # This is usually because of a TLE verdict caused by printing stuff after the interactor
            # has issued the AC verdict
            # This results in a TLE verdict getting full points, which should not be the case
            return False
        if not isinstance(self.check, CheckerResult):
            return CheckerResult(self.check, case.points if self.check else 0.0, feedback=self.feedback)
        return self.check

    def interact(self, case: TestCase, interactor: Interactor) -> CheckerOutput:
        raise NotImplementedError
