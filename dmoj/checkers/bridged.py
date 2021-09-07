import os
import shlex
import subprocess

from dmoj.contrib import contrib_modules
from dmoj.error import InternalError
from dmoj.judgeenv import env, get_problem_root
from dmoj.result import CheckerResult
from dmoj.utils.helper_files import compile_with_auxiliary_files, mktemp
from dmoj.utils.unicode import utf8text


def get_executor(problem_id, files, flags, lang, compiler_time_limit):
    if isinstance(files, str):
        filenames = [files]
    elif isinstance(files.unwrap(), list):
        filenames = list(files.unwrap())

    filenames = [os.path.join(get_problem_root(problem_id), f) for f in filenames]
    executor = compile_with_auxiliary_files(filenames, flags, lang, compiler_time_limit)

    return executor


def check(
    process_output,
    judge_output,
    judge_input,
    problem_id,
    files,
    lang,
    time_limit=env['generator_time_limit'],
    memory_limit=env['generator_memory_limit'],
    compiler_time_limit=env['generator_compiler_limit'],
    feedback=True,
    flags=[],
    type='default',
    args_format_string=None,
    point_value=None,
    **kwargs,
) -> CheckerResult:
    executor = get_executor(problem_id, files, flags, lang, compiler_time_limit)

    if type not in contrib_modules:
        raise InternalError('%s is not a valid contrib module' % type)

    args_format_string = args_format_string or contrib_modules[type].ContribModule.get_checker_args_format_string()

    with mktemp(judge_input) as input_file, mktemp(process_output) as output_file, mktemp(judge_output) as answer_file:
        checker_args = shlex.split(
            args_format_string.format(
                input_file=shlex.quote(input_file.name),
                output_file=shlex.quote(output_file.name),
                answer_file=shlex.quote(answer_file.name),
            )
        )
        process = executor.launch(
            *checker_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, memory=memory_limit, time=time_limit
        )

        proc_output, error = process.communicate()
        proc_output = utf8text(proc_output)

        return contrib_modules[type].ContribModule.parse_return_code(
            process,
            executor,
            point_value,
            time_limit,
            memory_limit,
            feedback=utf8text(proc_output) if feedback else '',
            name='checker',
            stderr=error,
        )
