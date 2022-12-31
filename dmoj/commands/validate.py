import os
import shlex
import subprocess
from itertools import groupby
from operator import itemgetter
from typing import List, Optional, Tuple


from dmoj import executors
from dmoj.commands.base_command import Command
from dmoj.contrib import contrib_modules
from dmoj.error import CompileError, InvalidCommandException, OutputLimitExceeded
from dmoj.judgeenv import env, get_problem_root, get_supported_problems
from dmoj.problem import BatchedTestCase, Problem, ProblemConfig, ProblemDataManager, TestCase
from dmoj.result import Result
from dmoj.utils.ansi import print_ansi
from dmoj.utils.helper_files import compile_with_auxiliary_files
from dmoj.utils.unicode import utf8text


all_executors = executors.executors


class ValidateCommand(Command):
    name = 'validate'
    help = 'Validates input for problems.'

    def _populate_parser(self) -> None:
        self.arg_parser.add_argument('problem_ids', nargs='+', help='ids of problems to validate input')

    def execute(self, line: str) -> int:
        args = self.arg_parser.parse_args(line)

        problem_ids = args.problem_ids
        supported_problems = set(get_supported_problems())

        unknown_problems = ', '.join(
            f"'{problem_id}'" for problem_id in problem_ids if problem_id not in supported_problems
        )
        if unknown_problems:
            raise InvalidCommandException(f'unknown problem(s) {unknown_problems}')

        total_fails = 0
        for problem_id in problem_ids:
            if not self.validate_problem(problem_id):
                print_ansi(f'Problem #ansi[{problem_id}](cyan|bold) #ansi[failed validation](red|bold).')
                total_fails += 1
            else:
                print_ansi(f'Problem #ansi[{problem_id}](cyan|bold) passed with flying colours.')
            print()

        print()
        print('Input validation complete.')
        if total_fails:
            print_ansi(f'#ansi[A total of {total_fails} problem(s) have invalid input.](red|bold)')
        else:
            print_ansi('#ansi[All problems validated.](green|bold)')

        return total_fails

    def validate_problem(self, problem_id: str) -> bool:
        print_ansi(f'Validating problem #ansi[{problem_id}](cyan|bold)...')

        problem_root = get_problem_root(problem_id)
        if problem_root is None:
            print_ansi(f'\t#ansi[Skipped](magenta|bold) - Problem [{problem_id}](cyan|bold) not found.')
            return True

        config = ProblemConfig(ProblemDataManager(problem_root))
        if not config.validator:
            print_ansi('\t#ansi[Skipped](magenta|bold) - No validator found.')
            return True

        validator_config = config['validator']
        language = validator_config['language']
        if language not in all_executors:
            print_ansi('\t\t#ansi[Skipped](magenta|bold) - Language not supported.')
            return True

        time_limit = validator_config.time_limit or env.validator_time_limit
        memory_limit = validator_config.memory_limit or env.validator_memory_limit
        compiler_time_limit = validator_config.get('compiler_time_limit', env.validator_compiler_time_limit)
        read_feedback_from = validator_config.get('read_feedback_from', 'stderr')
        if read_feedback_from not in ('stdout', 'stderr'):
            print_ansi('\t\t#ansi[Failed](red|bold) - Feedback option should be (stdout, stderr).')
            return False

        if isinstance(validator_config.source, str):
            filenames = [validator_config.source]
        elif isinstance(validator_config.source.unwrap(), list):
            filenames = list(validator_config.source.unwrap())
        else:
            print_ansi('\t#ansi[Failed](red|bold) - No validator found.')
            return False

        filenames = [os.path.abspath(os.path.join(problem_root, name)) for name in filenames]
        try:
            executor = compile_with_auxiliary_files(filenames, lang=language, compiler_time_limit=compiler_time_limit)
        except CompileError as compilation_error:
            print_ansi('#ansi[Failed compiling validator!](red|bold)')
            print(compilation_error.message.rstrip())
            return False

        problem = Problem(problem_id, time_limit, memory_limit, {})

        flattened_cases: List[Tuple[Optional[int], TestCase]] = []
        batch_number = 0
        for case in problem.cases():
            if isinstance(case, BatchedTestCase):
                batch_number += 1
                for batched_case in case.batched_cases:
                    assert isinstance(batched_case, TestCase)
                    flattened_cases.append((batch_number, batched_case))
            else:
                assert isinstance(case, TestCase)
                flattened_cases.append((None, case))

        contrib_type = validator_config.get('type', 'default')
        if contrib_type not in contrib_modules:
            print_ansi(f'#ansi[{contrib_type} is not a valid contrib module!](red|bold)')
            return False

        args_format_string = (
            validator_config.args_format_string
            or contrib_modules[contrib_type].ContribModule.get_validator_args_format_string()
        )

        case_number = 0
        ok = True
        for batch_number, cases in groupby(flattened_cases, key=itemgetter(0)):
            if batch_number:
                print_ansi(f'#ansi[Batch #{batch_number}](yellow|bold)')
            for _, case in cases:
                case_number += 1

                result = Result(case)
                input = case.input_data()

                validator_args = shlex.split(args_format_string.format(batch_no=case.batch, case_no=case.position))
                process = executor.launch(
                    *validator_args,
                    time=time_limit,
                    memory=memory_limit,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    wall_time=case.config.wall_time_factor * time_limit,
                )
                try:
                    proc_output, proc_error = process.communicate(
                        input, outlimit=case.config.output_limit_length, errlimit=1048576
                    )
                except OutputLimitExceeded:
                    proc_error = b''
                    process.kill()
                finally:
                    process.wait()

                executor.populate_result(proc_error, result, process)
                feedback = (
                    utf8text({'stdout': proc_output, 'stderr': proc_error}[read_feedback_from].rstrip())
                    or result.feedback
                )
                code = result.readable_codes()[0]
                code_colour = Result.COLORS_BYID[code]
                if code == 'AC':
                    code = 'OK'  # this is less confusing
                colored_code = f'#ansi[{code}]({code_colour}|bold)'
                colored_feedback = f'(#ansi[{utf8text(feedback)}](|underline))' if feedback else ''
                case_padding = '  ' if batch_number is not None else ''
                print_ansi(f'{case_padding}Test case {case_number:2d} {colored_code:3s} {colored_feedback}')

                if result.result_flag:
                    ok = False

        return ok
