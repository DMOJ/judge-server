import os
import subprocess

from dmoj.contrib import contrib_modules
from dmoj.error import InternalError
from dmoj.graders.standard import StandardGrader
from dmoj.judgeenv import env, get_problem_root
from dmoj.utils.helper_files import compile_with_auxiliary_files, mktemp
from dmoj.utils.unicode import utf8text


class BridgedInteractiveGrader(StandardGrader):
    def __init__(self, judge, problem, language, source):
        super().__init__(judge, problem, language, source)
        self.handler_data = self.problem.config.interactive
        self.interactor_binary = self._generate_interactor_binary()

    def check_result(self, case, result):
        if result.result_flag:
            # This is usually because of a TLE verdict raised after the interactor
            # has issued the AC verdict
            # This results in a TLE verdict getting full points, which should not be the case
            return False

        stderr = self._interactor.stderr.read()
        return_code = self.handler_data.get('type', 'default')
        if return_code not in contrib_modules:
            raise InternalError('%s is not a valid return code parser' % return_code)

        return contrib_modules[return_code].ContribModule.parse_return_code(
            self._interactor,
            self.interactor_binary,
            case.points,
            self._interactor_time_limit,
            self._interactor_memory_limit,
            feedback=utf8text(stderr) if self.handler_data.feedback else None,
            name='interactor',
            stderr=stderr,
        )

    def _launch_process(self, case):
        self._interactor_stdin_pipe, submission_stdout_pipe = os.pipe()
        submission_stdin_pipe, self._interactor_stdout_pipe = os.pipe()
        self._current_proc = self.binary.launch(
            time=self.problem.time_limit,
            memory=self.problem.memory_limit,
            symlinks=case.config.symlinks,
            stdin=submission_stdin_pipe,
            stdout=submission_stdout_pipe,
            stderr=subprocess.PIPE,
            wall_time=case.config.wall_time_factor * self.problem.time_limit,
        )
        os.close(submission_stdin_pipe)
        os.close(submission_stdout_pipe)

    def _interact_with_process(self, case, result, input):
        output = case.output_data()
        self._interactor_time_limit = (self.handler_data.preprocessing_time or 0) + self.problem.time_limit
        self._interactor_memory_limit = self.handler_data.memory_limit or env['generator_memory_limit']

        with mktemp(input) as input_file, mktemp(output) as output_file:
            self._interactor = self.interactor_binary.launch(
                input_file.name,
                output_file.name,
                time=self._interactor_time_limit,
                memory=self._interactor_memory_limit,
                stdin=self._interactor_stdin_pipe,
                stdout=self._interactor_stdout_pipe,
                stderr=subprocess.PIPE,
            )

            os.close(self._interactor_stdin_pipe)
            os.close(self._interactor_stdout_pipe)

            self._current_proc.wait()
            self._interactor.wait()

            return self._current_proc.stderr.read()

    def _generate_interactor_binary(self):
        files = self.handler_data.files
        if not isinstance(files, list):
            files = [files]
        files = [os.path.join(get_problem_root(self.problem.id), f) for f in files]
        return compile_with_auxiliary_files(files, self.handler_data.lang, self.handler_data.compiler_time_limit)
