import argparse
import os
import sys

import yaml

from dmoj.config import ConfigNode

problem_dirs = ()
env = ConfigNode(defaults={
    'selftest_sandboxing': True,
    'runtime': {},
}, dynamic=False)
_root = os.path.dirname(__file__)
fs_encoding = os.environ.get('DMOJ_ENCODING', sys.getfilesystemencoding())

log_file = server_host = server_port = no_ansi = no_ansi_emu = no_watchdog = problem_regex = case_regex = None

startup_warnings = []

only_executors = set()
exclude_executors = set()


def unicodify(string):
    if isinstance(string, str):
        return string.decode(fs_encoding)
    return string


def load_env(cli=False, testsuite=False):  # pragma: no cover
    global problem_dirs, only_executors, exclude_executors, log_file, server_host, \
        server_port, no_ansi, no_ansi_emu, env, startup_warnings, no_watchdog, \
        problem_regex, case_regex
    _parser = argparse.ArgumentParser(description='''
        Spawns a judge for a submission server.
    ''')
    if not cli:
        _parser.add_argument('server_host', help='host to listen for the server')
        _parser.add_argument('judge_name', nargs='?', help='judge name (overrides configuration)')
        _parser.add_argument('judge_key', nargs='?', help='judge key (overrides configuration)')
        _parser.add_argument('-p', '--server-port', type=int, default=9999,
                             help='port to listen for the server')
    _parser.add_argument('-c', '--config', type=str, default=None, required=True,
                         help='file to load judge configurations from')

    if not cli:
        _parser.add_argument('-l', '--log-file',
                             help='log file to use')
        _parser.add_argument('--no-watchdog', action='store_true',
                             help='disable use of watchdog on problem directories')

    _group = _parser.add_mutually_exclusive_group()
    _group.add_argument('-e', '--only-executors',
                        help='only listed executors will be loaded (comma-separated)')
    _group.add_argument('-x', '--exclude-executors',
                        help='prevent listed executors from loading (comma-separated)')

    _parser.add_argument('--no-ansi', action='store_true', help='disable ANSI output')
    if os.name == 'nt':
        _parser.add_argument('--no-ansi-emu', action='store_true', help='disable ANSI emulation on Windows')

    if testsuite:
        _parser.add_argument('tests_dir', help='directory where tests are stored')
        _parser.add_argument('problem_regex', help='when specified, only matched problems will be tested', nargs='?')
        _parser.add_argument('case_regex', help='when specified, only matched cases will be tested', nargs='?')

    _args = _parser.parse_args()

    server_host = getattr(_args, 'server_host', None)
    server_port = getattr(_args, 'server_port', None)

    no_ansi_emu = _args.no_ansi_emu if os.name == 'nt' else True
    no_ansi = _args.no_ansi
    no_watchdog = True if cli else _args.no_watchdog

    log_file = getattr(_args, 'log_file', None)
    only_executors |= _args.only_executors and set(_args.only_executors.split(',')) or set()
    exclude_executors |= _args.exclude_executors and set(_args.exclude_executors.split(',')) or set()

    model_file = _args.config

    with open(model_file) as init_file:
        env.update(yaml.safe_load(init_file))

        if getattr(_args, 'judge_name', None):
            env['id'] = _args.judge_name

        if getattr(_args, 'judge_key', None):
            env['key'] = _args.judge_key

        dirs = env.problem_storage_root
        if dirs is None:
            return

        if isinstance(dirs, ConfigNode):
            problem_dirs = tuple(unicodify(os.path.normpath(os.path.join(_root, dir))) for dir in dirs)
        else:
            problem_dirs = os.path.join(_root, dirs)
            problem_dirs = [unicodify(os.path.normpath(os.path.join(problem_dirs, dir)))
                            for dir in os.listdir(problem_dirs)]
            problem_dirs = tuple(dir for dir in problem_dirs if os.path.isdir(dir))

        cleaned_dirs = []
        for dir in problem_dirs:
            if not os.path.exists(dir) or not os.path.isdir(dir):
                startup_warnings.append('cannot access problem directory %s (does it exist?)' % dir)
                continue
            cleaned_dirs.append(dir)
        problem_dirs = cleaned_dirs

    if testsuite:
        if not os.path.isdir(_args.tests_dir):
            raise SystemExit('Invalid tests directory')
        problem_dirs = [_args.tests_dir]

        import re
        if _args.problem_regex:
            try:
                problem_regex = re.compile(_args.problem_regex)
            except re.error:
                raise SystemExit('Invalid problem regex')
        if _args.case_regex:
            try:
                case_regex = re.compile(_args.case_regex)
            except re.error:
                raise SystemExit('Invalid case regex')


def get_problem_root(pid):
    for dir in problem_dirs:
        path = os.path.join(dir, pid)
        if os.path.exists(path):
            return path
    return None


def get_problem_roots():
    return problem_dirs


def get_supported_problems():
    """
    Fetches a list of all problems supported by this judge.
    :return:
        A list of all problems in tuple format: (problem id, mtime)
    """
    problems = []
    for dir in get_problem_roots():
        for problem in os.listdir(dir):
            if isinstance(problem, str):
                problem = problem.decode(fs_encoding)
            if os.access(os.path.join(dir, problem, 'init.yml'), os.R_OK):
                problems.append((problem, os.path.getmtime(os.path.join(dir, problem))))
    return problems


def get_runtime_versions():
    from dmoj.executors import executors
    return {name: clazz.Executor.get_runtime_versions() for name, clazz in executors.iteritems()}