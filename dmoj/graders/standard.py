from __future__ import print_function

import gc
import logging
import os
import platform
import signal

import six

from dmoj.error import CompileError
from dmoj.executors import executors
from dmoj.graders.base import BaseGrader
from dmoj.result import Result, CheckerResult
from dmoj.utils.communicate import OutputLimitExceeded
from dmoj.utils.error import print_protection_fault

try:
    from dmoj.utils.nixutils import strsignal
except ImportError:
    try:
        from dmoj.utils.winutils import strsignal
    except ImportError:
        strsignal = lambda x: 'signal %s' % x

log = logging.getLogger('dmoj.graders')


class StandardGrader(BaseGrader):
    def grade(self, case):
        result = Result(case)

        input = case.input_data()  # cache generator data

        self._current_proc = self.binary.launch(time=self.problem.time_limit, memory=self.problem.memory_limit,
                                                pipe_stderr=True, unbuffered=case.config.unbuffered,
                                                io_redirects=case.io_redirects(),
                                                wall_time=case.config.wall_time_factor * self.problem.time_limit)

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
        result.feedback = (check.feedback or (process.feedback if hasattr(process, 'feedback') else
                            getattr(self.binary, 'get_feedback', lambda x, y, z: '')(error, result, process)))
        if not result.feedback and result.get_main_code() == Result.RTE:
            if hasattr(process, 'was_initialized') and not process.was_initialized:
                # Process may failed to initialize, resulting in a SIGKILL without any prior signals.
                # See <https://github.com/DMOJ/judge/issues/179> for more details.
                result.feedback = 'failed initializing'
            elif hasattr(process, 'signal'):
                # I suppose generate a SIGKILL message is better when we don't know the signal that caused it.
                result.feedback = strsignal(process.signal).lower() if process.signal else 'killed'

        # On Linux we can provide better help messages
        if hasattr(process, 'protection_fault') and process.protection_fault:
            syscall, callname, args = process.protection_fault
            print_protection_fault(process.protection_fault)
            callname = callname.replace('sys_', '', 1)
            message = {
                'open': 'opening files is not allowed',
            }.get(callname, '%s syscall disallowed' % callname)
            result.feedback = message

    def check_result(self, case, result):
        # If the submission didn't crash and didn't time out, there's a chance it might be AC
        # We shouldn't run checkers if the submission is already known to be incorrect, because some checkers
        # might be very computationally expensive.
        # See https://github.com/DMOJ/judge/issues/170
        if not result.result_flag:
            # Checkers might crash if any data is None, so force at least empty string
            check = case.checker()(result.proc_output or b'',
                                   case.output_data() or b'',
                                   submission_source=self.source,
                                   judge_input=case.input_data() or b'',
                                   point_value=case.points,
                                   case_position=case.position,
                                   batch=case.batch,
                                   submission_language=self.language)
        else:
            # Solution is guaranteed to receive 0 points
            check = False

        return check

    def set_result_flag(self, process, result):
        if process.returncode > 0:
            if os.name == 'nt' and process.returncode == 3:
                # On Windows, abort() causes return value 3, instead of SIGABRT.
                result.result_flag |= Result.RTE
                process.signal = signal.SIGABRT
            elif os.name == 'nt' and process.returncode == 0xC0000005:
                # On Windows, 0xC0000005 is access violation (SIGSEGV).
                result.result_flag |= Result.RTE
                process.signal = signal.SIGSEGV
            else:
                # print>> sys.stderr, 'Exited with error: %d' % process.returncode
                result.result_flag |= Result.IR
        if process.returncode < 0:
            # None < 0 == True
            # if process.returncode is not None:
            # print('Killed by signal %d' % -process.returncode, file=sys.stderr)
            result.result_flag |= Result.RTE  # Killed by signal
        if process.tle:
            result.result_flag |= Result.TLE
        if process.mle:
            result.result_flag |= Result.MLE

    def _interact_with_process(self, case, result, input):
        process = self._current_proc
        try:
            result.proc_output, error = process.safe_communicate(input, outlimit=case.config.output_limit_length,
                                                                 errlimit=1048576)
        except OutputLimitExceeded as ole:
            stream, result.proc_output, error = ole.args
            log.warning('OLE on stream: %s', stream)
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
            binary = executors[self.language].Executor(self.problem.id, self.source,
                                                       hints=self.problem.config.hints or [])
        except CompileError as compilation_error:
            error = compilation_error.args[0]
            error = error.decode('mbcs') if os.name == 'nt' and isinstance(error, six.binary_type) else error
            self.judge.packet_manager.compile_error_packet(ansi.format_ansi(error or ''))

            # Compile error is fatal
            raise

        # Carry on grading in case of compile warning
        if hasattr(binary, 'warning') and binary.warning:
            self.judge.packet_manager.compile_message_packet(ansi.format_ansi(binary.warning or ''))
        return binary
