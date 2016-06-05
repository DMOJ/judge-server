import os
from functools import partial

from dmoj.error import CompileError
from dmoj.executors import executors
from dmoj.graders.base import BaseGrader
from dmoj.result import Result, CheckerResult
from dmoj.utils.communicate import safe_communicate, OutputLimitExceeded

try:
    from dmoj.utils.nixutils import strsignal
except ImportError:
    strsignal = lambda x: ''


class StandardGrader(BaseGrader):
    def grade(self, case):
        result = Result(case)

        input = case.input_data()  # cache generator data

        self._current_proc = self.binary.launch(time=self.problem.time_limit, memory=self.problem.memory_limit,
                                                pipe_stderr=True, unbuffered=case.config.unbuffered)

        error = self._interact_with_process(case, result, input)

        process = self._current_proc

        result.max_memory = process.max_memory or 0.0
        result.execution_time = process.execution_time or 0.0
        result.r_execution_time = process.r_execution_time or 0.0

        # Translate status codes/process results into Result object for status codes
        self.set_result_flag(process, result)

        check = self.check_result(case, result)

        # checkers must either return a boolean (True: full points, False: 0 points)
        # or a CheckerResult, so convert to CheckerResult if it returned bool
        if not isinstance(check, CheckerResult):
            check = CheckerResult(check, case.points if check else 0.0)

        result.result_flag |= [Result.WA, Result.AC][check.passed]
        result.points = check.points

        self.update_feedback(check, error, process, result)

        return result

    def update_feedback(self, check, error, process, result):
        result.feedback = (check.feedback or
                           (process.feedback if hasattr(process, 'feedback') else
                            getattr(self.binary, 'update_feedback', lambda x, y, z: '')(error, result, process)))
        if not result.feedback and hasattr(process, 'signal') and process.signal and result.get_main_code() in [
            Result.IR, Result.RTE]:
            result.feedback = strsignal(process.signal)

        # On Linux we can provide better help messages
        if hasattr(process, 'protection_fault') and process.protection_fault:
            sigid, callname = process.protection_fault
            callname = callname.replace('sys_', '', 1)
            message = {
                'open': 'opening files is not allowed',
                'socketcall': 'accessing the network is not allowed',
                'socket': 'accessing the network is not allowed',
                'clone': 'threading is not allowed'
            }.get(callname, '%s syscall disallowed' % callname)
            result.feedback = message

    def check_result(self, case, result):
        # If the submission didn't crash and didn't time out, there's a chance it might be AC
        # We shouldn't run checkers if the submission is already known to be incorrect, because some checkers
        # might be very computationally expensive.
        # See https://github.com/DMOJ/judge/issues/170
        if not result.result_flag:
            # Checkers might crash if any data is None, so force at least empty string
            check = case.checker()(result.proc_output or '',
                                   case.output_data() or '',
                                   submission_source=self.source,
                                   judge_input=case.input_data() or '',
                                   point_value=case.points,
                                   case_position=case.position)
        else:
            # Solution is guaranteed to receive 0 points
            check = False

        return check

    def set_result_flag(self, process, result):
        if process.returncode > 0:
            # print>> sys.stderr, 'Exited with error: %d' % process.returncode
            result.result_flag |= Result.IR
        if process.returncode < 0:
            # None < 0 == True
            # if process.returncode is not None:
            # print>> sys.stderr, 'Killed by signal %d' % -process.returncode
            result.result_flag |= Result.RTE  # Killed by signal
        if process.tle:
            result.result_flag |= Result.TLE
        if process.mle:
            result.result_flag |= Result.MLE

    def _interact_with_process(self, case, result, input):
        process = self._current_proc
        communicate = process.safe_communicate if hasattr(process, 'safe_communicate') else partial(safe_communicate,
                                                                                                    process)
        try:
            result.proc_output, error = communicate(input, outlimit=case.config.output_limit_length, errlimit=1048576)
        except OutputLimitExceeded as ole:
            stream, result.proc_output, error = ole.args
            print 'OLE:', stream
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
        from dmoj.utils import ansi

        # If the executor requires compilation, compile and send any errors/warnings to the site
        try:
            # Fetch an appropriate executor for the language
            binary = executors[self.language].Executor(self.problem.id, self.source)
        except CompileError as compilation_error:
            error = compilation_error.args[0]
            error = error.decode('mbcs') if os.name == 'nt' and isinstance(error, str) else error
            self.judge.packet_manager.compile_error_packet(ansi.format_ansi(error or ''))

            # Compile error is fatal
            raise

        # Carry on grading in case of compile warning
        if hasattr(binary, 'warning') and binary.warning:
            self.judge.packet_manager.compile_message_packet(ansi.format_ansi(binary.warning or ''))
        return binary
