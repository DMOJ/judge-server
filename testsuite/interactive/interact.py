from dmoj.graders.interactive import InteractiveGrader

class Grader(InteractiveGrader):
    def interact(self, case, interactor):
        N = int(case.input_data())
        guess = None
        guesses = 0
        while True:
            guesses += 1
            guess = interactor.readint()
            if guess == N:
                break
            interactor.writeln(N - guess)
        return guesses < 10
