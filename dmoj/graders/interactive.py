from dmoj.graders.standard import StandardGrader

class Interactor(object):
    def __init__(self, process):
        self.process = process

    def read(self):
        return self.process.stdout.read()

    def readline(self):
        return self.process.stdout.readline()

    def write(self, str):
        self.process.stdin.write(str)
        self.process.stdin.flush()
        
    def writeln(self, str):
        write(str + '\n')
        
    def close(self):
        for stream in [self.process.stdin, self.process.stdout, self.process.stderr]:
            stream.close()

class InteractiveGrader(StandardGrader):
    def _interact_with_process(self, case, result, input):
        interactor = Interactor(self._current_proc)
        try:
            self.check = self.interact(interactor)
            interactor.close()
        except NotImplementedError as e:
            # it is not the user's fault that the problemsetter was incompetent
            raise e
        except:
            self.check = False

        self.process.wait()
        
    def interact():
        raise NotImplementedError
        
