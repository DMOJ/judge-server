import os
import subprocess

from dmoj.graders.standard import StandardGrader
from dmoj.judgeenv import env, get_problem_root
from dmoj.utils.helper_files import compile_with_auxiliary_files, mktemp, parse_helper_file_error
from dmoj.utils.unicode import utf8text


class BridgedInteractiveGrader(StandardGrader):
    def __init__(self, judge, problem, language, source, meta):
        super().__init__(judge, problem, language, source, meta)
        self.handler_data = self.problem.config.interactive
        self.interactor_binary = self._generate_interactor_binary()

    def check_result(self, case, result):
        if result.result_flag:
            # This is usually because of a TLE verdict raised after the interactor
            # has issued the AC verdict
            # This results in a TLE verdict getting full points, which should not be the case
            return False

        stderr = self._interactor.stderr.read()
        # We use the testlib.h return codes
        AC = 0
        WA = 1
        PE = 2
        IE = 3

        if process.returncode == AC:
            if feedback:
                return CheckerResult(True, point_value, feedback=proc_output)
            else:
                return CheckerResult(True, point_value)
        elif process.returncode in (WA, PE):
            if feedback:
                return CheckerResult(False, 0, feedback=proc_output)
            else:
                return CheckerResult(False, 0, feedback='Presentation Error' if process.returncode == PE else '')
        else:
            if process.returncode == IE:
                error = 'checker failed assertion with message %s' % proc_output
            else:
                parse_helper_file_error(self._interactor, self._interactor_binary, name='interactor', stderr=stderr,
                                        time_limit=self._interactor_time_limit,
                                        memory_limit=self._interactor_memory_limit)

    def _launch_process(self, case):
        submission_stdin, self._stdout_pipe = os.pipe()
        self._stdin_pipe, submission_stdout = os.pipe()
        self._current_proc = self.binary.launch(
            time=self.problem.time_limit, memory=self.problem.memory_limit, symlinks=case.config.symlinks,
            stdin=submission_stdin, stdout=submission_stdout, stderr=subprocess.PIPE,
            wall_time=case.config.wall_time_factor * self.problem.time_limit,
        )
        os.close(submission_stdin)
        os.close(submission_stdout)

    def _interact_with_process(self, case, result, input):
        output = case.output_data()
        self._interactor_time_limit = (self.handler_data.preprocessing_time or 0) + self.problem.time_limit
        self._interactor_memory_limit = self.handler_data.memory_limit or env['generator_memory_limit']

        with mktemp(input) as input_file, mktemp(output) as output_file:
            self._interactor = self.interactor_binary.launch(
                input_file.name, output_file.name, time=self._interactor_time_limit,
                memory=self._interactor_memory_limit, stdin=self._stdin_pipe, stdout=self._stdout_pipe,
                stderr=subprocess.PIPE,
            )

            os.close(self._stdin_pipe)
            os.close(self._stdout_pipe)

            self._current_proc.wait()
            self._interactor.wait()

            return self._current_proc.stderr.read()

    def _generate_interactor_binary(self):
        files = self.handler_data.files
        if not isinstance(files, list):
            files = [files]
        files = [os.path.join(get_problem_root(self.problem.id), f) for f in files]
        return compile_with_auxiliary_files(files, self.handler_data.lang, self.handler_data.compiler_time_limit)
