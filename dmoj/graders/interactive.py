from dmoj.graders.standard import StandardGrader

class WrongAnswer(BaseException):
    pass

class Interactor(object):
    def __init__(self, process):
        self.process = process
        self._tokens = None

    def read(self):
        return self.process.stdout.read()

    def readln(self, strip_newline=True):
        ret = self.process.stdout.readline()
        if strip_newline:
            return ret.rstrip()
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
        try:
            ret = int(self.readtoken(delim))
        except ValueError:
            raise WrongAnswer
        if not lo <= ret <= hi:
            raise WrongAnswer
        return ret

    def readfloat(self, lo=float('-inf'), hi=float('inf'), delim=None):
        try:
            ret = float(self.readtoken(delim))
        except ValueError:
            raise WrongAnswer
        if not lo <= ret <= hi:
            raise WrongAnswer
        return ret

    def write(self, str):
        self.process.stdin.write(str)
        self.process.stdin.flush()

    def writeln(self, str):
        self.write(str + '\n')

    def close(self):
        for stream in [self.process.stdin, self.process.stdout, self.process.stderr]:
            try:
                stream.close()
            except IOError:
                pass

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
