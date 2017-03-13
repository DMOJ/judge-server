from dmoj.graders.interactive import InteractiveGrader

def Grader(InteractiveGrader):
    def interact(self, case, interactor):
        N = int(case.input_data())
        guess = None
        guesses = 0
        while guess != N:
            guess = interactor.readint()
            interactor.writeln(N - guess)
            guesses += 1
        return guesses < 10
