from dmoj.graders.interactive import InteractiveGrader

class Grader(InteractiveGrader):
    def interact(self, case, interactor):
        N = int(case.input_data())
        guesses = 0
        guess = 0
        while guess != N:
            guess = interactor.readint(1, 2000000000)
            guesses += 1
            if guess == N:
                interactor.writeln('OK')
            elif guess > N:
                interactor.writeln('FLOATS')
            else:
                interactor.writeln('SINKS')
        return guesses <= 31
