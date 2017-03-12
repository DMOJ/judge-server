from dmoj.graders.standard import StandardGrader

class Interactor(object):
    def __init__(self, process):
        self.process = process
        self._is_closed = False

    def read(self):
        return self.process.stdout.read()

    def readln(self):
        return self.process.stdout.readline()

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
        except:
            pass

        self._current_proc.wait()

    def check_result(self, case, result):
        return self.check

