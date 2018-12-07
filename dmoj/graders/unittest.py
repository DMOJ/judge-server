from dmoj.graders.standard import StandardGrader
from dmoj.judgeenv import get_problem_root
from dmoj.error import CompileError
from dmoj.executors import executors
import os

# Change on unittest module is needed for unittest to run properly.
# Diff goes:
#
# --- main.py2    2018-12-07 18:00:00.000000000 +0000
# +++ main.py     2018-12-07 17:59:00.000000000 +0000
# @@ -230,7 +230,7 @@
#              # it is assumed to be a TestRunner instance
#              testRunner = self.testRunner
#          self.result = testRunner.run(self.test)
# -        if self.exit:
# +        if not self.result.wasSuccessful():
#              sys.exit(not self.result.wasSuccessful())
# 
#  main = TestProgram
#

class UnitTestGrader(StandardGrader):
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
                                   submission_language=self.language,
                                   binary_data=case.has_binary_data)
        else:
            # Solution is guaranteed to receive 0 points
            check = False

        return check

    def _interact_with_process(self, case, result, input):
        process = self._current_proc
        try:
            result.proc_output, error = process.safe_communicate('', outlimit=case.config.output_limit_length,
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
        unitTestFile = open(os.path.join(get_problem_root(self.problem.id), self.problem.config['unit_test']),'r')
        unitTestCode = unitTestFile.read()
        unitTestFile.close()
        from dmoj.utils import ansi

        # If the executor requires compilation, compile and send any errors/warnings to the site
        try:
            # Fetch an appropriate executor for the language
            binary = executors[self.language].Executor(self.problem.id, self.source + '\n\n' + unitTestCode,
                                                       hints=self.problem.config.hints or [],
                                                       unbuffered=self.problem.config.unbuffered)
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
