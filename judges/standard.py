from functools import partial
import sys

from communicate import safe_communicate, OutputLimitExceeded

from error import CompileError
from executors import executors
from executors.base_executor import CompiledExecutor
from judge import format_ansi, CheckerResult
from judges.base import BaseGrader
from result import Result


class StandardGrader(BaseGrader):
    def grade(self, case):
        result = Result()
        result.case = case

        self._current_proc = self.binary.launch(time=self.problem.time_limit, memory=self.problem.memory_limit,
                                                pipe_stderr=True,
                                                unbuffered=case.config.unbuffered)

        error = self._interact_with_process(case, result)

        process = self._current_proc

        result.max_memory = process.max_memory or 0.0
        result.execution_time = process.execution_time or 0.0
        result.r_execution_time = process.r_execution_time or 0.0

        # C standard checker will crash if not given a string
        proc_output = result.proc_output or ''

        check = case.checker()(proc_output, case.output_data(),
                               submission_source=self.source,
                               judge_input=case.input_data(),
                               point_value=case.points)

        # checkers must either return a boolean (True: full points, False: 0 points)
        # or a CheckerResult, so convert to CheckerResult if it returned bool
        if not isinstance(check, CheckerResult):
            check = CheckerResult(check, case.points if check else 0.0)

        result.result_flag |= [Result.WA, Result.AC][check.passed]

        # Translate status codes/process results into Result object for status codes
        if not case.config.swallow_ir and process.returncode > 0:
            print>> sys.stderr, 'Exited with error: %d' % process.returncode
            result.result_flag |= Result.IR
        if not case.config.swallow_rte and process.returncode < 0:
            # None < 0 == True
            if process.returncode is not None:
                print>> sys.stderr, 'Killed by signal %d' % -process.returncode
            result.result_flag |= Result.RTE  # Killed by signal
        if not case.config.swallow_tle and process.tle:
            result.result_flag |= Result.TLE
        if process.mle:
            result.result_flag |= Result.MLE

        if result.result_flag & ~Result.WA:
            check.points = 0

        result.points = check.points
        result.feedback = (check.feedback or
                           (process.feedback if hasattr(process, 'feedback') else
                            getattr(self.binary, 'get_feedback', lambda x, y: '')(error, result)))

        return result

    def _interact_with_process(self, case, result):
        process = self._current_proc
        communicate = process.safe_communicate if hasattr(process, 'safe_communicate') else partial(safe_communicate,
                                                                                                    process)
        try:
            result.proc_output, error = communicate(case.input_data(), outlimit=25165824, errlimit=1048576)
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
        # If the executor requires compilation, compile and send any errors/warnings to the site
        executor = executors[self.language].Executor
        if issubclass(executor, CompiledExecutor):
            try:
                # Fetch an appropriate executor for the language
                binary = executor(self.problem.id, self.source)
            except CompileError as compilation_error:
                self.judge.packet_manager.compile_error_packet(compilation_error.message)

                # Compile error is fatal
                return None
        else:
            binary = executor(self.problem.id, self.source)

        # Carry on grading in case of compile warning
        if hasattr(binary, 'warning') and binary.warning:
            self.judge.packet_manager.compile_message_packet(format_ansi(binary.warning))
        return binary


