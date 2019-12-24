import gc
import logging
import platform
import subprocess

from dmoj.error import OutputLimitExceeded
from dmoj.executors import executors
from dmoj.graders.base import BaseGrader
from dmoj.result import CheckerResult, Result

log = logging.getLogger('dmoj.graders')


class StandardGrader(BaseGrader):
    def grade(self, case):
        result = Result(case)

        input = case.input_data()  # cache generator data

        self._launch_process(case)

        error = self._interact_with_process(case, result, input)

        process = self._current_proc

        result.max_memory = process.max_memory or 0.0
        result.execution_time = process.execution_time or 0.0
        result.wall_clock_time = process.wall_clock_time or 0.0

        # Translate status codes/process results into Result object for status codes
        result.set_result_flag(process)

        check = self.check_result(case, result)

        # checkers must either return a boolean (True: full points, False: 0 points)
        # or a CheckerResult, so convert to CheckerResult if it returned bool
        if not isinstance(check, CheckerResult):
            check = CheckerResult(check, case.points if check else 0.0)

        result.result_flag |= [Result.WA, Result.AC][check.passed]
        result.points = check.points
        result.extended_feedback = check.extended_feedback

        self.update_feedback(check, error, process, result)
        case.free_data()

        # Where CPython has reference counting and a GC, PyPy only has a GC. This means that while CPython
        # will have freed any (usually massive) generated data from the line above by reference counting, it might
        # - and probably still is - in memory by now. We need to be able to fork() immediately, which has a good chance
        # of failing if there's not a lot of swap space available.
        #
        # We don't really have a way to force the generated data to disappear, so calling a gc here is the best
        # chance we have.
        if platform.python_implementation() == 'PyPy':
            gc.collect()

        return result

    def update_feedback(self, check, error, process, result):
        result.update_feedback(error, process, self.binary, check.feedback)

    def check_result(self, case, result):
        # If the submission didn't crash and didn't time out, there's a chance it might be AC
        # We shouldn't run checkers if the submission is already known to be incorrect, because some checkers
        # might be very computationally expensive.
        # See https://github.com/DMOJ/judge/issues/170
        checker = case.checker()
        # checker is a `partial` object, NOT a `function` object
        if not result.result_flag or getattr(checker.func, 'run_on_error', False):
            try:
                # Checkers might crash if any data is None, so force at least empty string
                check = checker(result.proc_output or b'',
                                case.output_data() or b'',
                                submission_source=self.source,
                                judge_input=case.input_data() or b'',
                                point_value=case.points,
                                case_position=case.position,
                                batch=case.batch,
                                submission_language=self.language,
                                binary_data=case.has_binary_data,
                                execution_time=result.execution_time,
                                problem_id=self.problem.id)
            except UnicodeDecodeError:
                # Don't rely on problemsetters to do sane things when it comes to Unicode handling, so
                # just proactively swallow all Unicode-related checker errors.
                return CheckerResult(False, 0, feedback='invalid unicode')
        else:
            # Solution is guaranteed to receive 0 points
            check = False

        return check

    def _launch_process(self, case):
        self._current_proc = self.binary.launch(
            time=self.problem.time_limit, memory=self.problem.memory_limit, symlinks=case.config.symlinks,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            wall_time=case.config.wall_time_factor * self.problem.time_limit,
        )

    def _interact_with_process(self, case, result, input):
        process = self._current_proc
        try:
            result.proc_output, error = process.communicate(input, outlimit=case.config.output_limit_length,
                                                            errlimit=1048576)
        except OutputLimitExceeded:
            error = None
            result.result_flag |= Result.OLE
            try:
                process.kill()
            except RuntimeError as e:
                if e.args[0] != 'TerminateProcess: 5':
                    raise
            # Otherwise it's a race between this kill and the shocker,
            # and failed kill means nothing.
            process.wait()
        return error

    def _generate_binary(self):
        return executors[self.language].Executor(self.problem.id, self.source,
                                                 hints=self.problem.config.hints or [],
                                                 unbuffered=self.problem.config.unbuffered)
