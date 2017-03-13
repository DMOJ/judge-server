from dmoj.graders.standard import StandardGrader

class WrongAnswer(BaseException):
    pass

class Interactor(object):
    def __init__(self, process):
        self.process = process
        self._is_closed = False
        self._tokens = None

    def read(self):
        return self.process.stdout.read()

    def readln(self):
        return self.process.stdout.readline()

    def readtoken(self, str=None):
        if not self._tokens:
            self._tokens = self.readln()
        try:
            ret, self._tokens = self._tokens.split(str, 1)
        except ValueError:
            ret = self._tokens
            self._tokens = None
        return ret

    def readint(self, lo=float('-inf'), hi=float('inf'), str=None):
        try:
            ret = int(self.readtoken(str))
        except ValueError:
            raise WrongAnswer
        if lo > ret or ret > hi:
            raise WrongAnswer
        return ret

    def readfloat(self, lo=float('-inf'), hi=float('inf'), str=None):
        try:
            ret = float(self.readtoken(str))
        except ValueError:
            raise WrongAnswer
        if lo > ret or ret > hi:
            raise WrongAnswer
        return ret
    def write(self, str):
        self.process.stdin.write(str)
        self.process.stdin.flush()

    def writeln(self, str):
        self.write(str + '\n')

    def close(self):
        if not self._is_closed:
            for stream in [self.process.stdin, self.process.stdout, self.process.stderr]:
                stream.close()
            self._is_closed = True

class InteractiveGrader(StandardGrader):
    def _interact_with_process(self, case, result, input):
        interactor = Interactor(self._current_proc)
        self.check = False
        try:
            self.check = self.interact(interactor)
            interactor.close()
        except WrongAnswer:
            pass

        self._current_proc.wait()

    def check_result(self, case, result):
        return self.check

    def interact(self, interactor):
        raise NotImplementedError
