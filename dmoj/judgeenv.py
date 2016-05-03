import argparse
import os
import sys

import yaml

__all__ = ['env', 'get_problem_root', 'get_problem_roots', 'only_executors', 'exclude_executors', 'log_file',
           'server_port', 'server_host', 'no_ansi', 'no_ansi_emu']

_judge_dirs = ()
env = {}
_root = os.path.dirname(__file__)
fs_encoding = os.environ.get('DMOJ_ENCODING', sys.getfilesystemencoding())

log_file = server_host = server_port = no_ansi = no_ansi_emu = None

only_executors = set()
exclude_executors = set()


def unicodify(string):
    if isinstance(string, str):
        return string.decode(fs_encoding)
    return string


def load_env():
    global _judge_dirs, only_executors, exclude_executors, log_file, server_host, server_port, no_ansi, no_ansi_emu, env
    _parser = argparse.ArgumentParser(description='''
        Spawns a judge for a submission server.
    ''')
    _parser.add_argument('server_host', help='host to listen for the server')
    _parser.add_argument('judge_name', nargs='?', help='judge name (overrides configuration)')
    _parser.add_argument('judge_key', nargs='?', help='judge key (overrides configuration)')
    _parser.add_argument('-p', '--server-port', type=int, default=9999,
                         help='port to listen for the server')
    _parser.add_argument('-c', '--config', type=str, default=None, required=True,
                         help='file to load judge configurations from')
    _parser.add_argument('-l', '--log-file',
                         help='log file to use')

    _group = _parser.add_mutually_exclusive_group()
    _group.add_argument('-e', '--only-executors',
                        help='only listed executors will be loaded (comma-separated)')
    _group.add_argument('-x', '--exclude-executors',
                        help='prevent listed executors from loading (comma-separated)')

    _parser.add_argument('--no-ansi', action='store_true', help='disable ANSI output')
    if os.name == 'nt':
        _parser.add_argument('--no-ansi-emu', action='store_true', help='disable ANSI emulation on Windows')

    _args = _parser.parse_args()

    server_host = _args.server_host
    server_port = _args.server_port

    no_ansi_emu = _args.no_ansi_emu if os.name == 'nt' else True
    no_ansi = _args.no_ansi

    log_file = _args.log_file
    only_executors |= _args.only_executors and set(_args.only_executors.split(',')) or set()
    exclude_executors |= _args.exclude_executors and set(_args.exclude_executors.split(',')) or set()

    model_file = _args.config

    with open(model_file) as init_file:
        env.update(yaml.safe_load(init_file))

        if _args.judge_name is not None:
            env['id'] = _args.judge_name

        if _args.judge_key is not None:
            env['key'] = _args.judge_key

        dirs = env.get('problem_storage_root', os.path.join('data', 'problems'))
        if isinstance(dirs, list):
            _judge_dirs = tuple(unicodify(os.path.normpath(os.path.join(_root, dir))) for dir in dirs)
        else:
            _judge_dirs = os.path.join(_root, dirs)
            _judge_dirs = [unicodify(os.path.normpath(os.path.join(_judge_dirs, dir)))
                           for dir in os.listdir(_judge_dirs)]
            _judge_dirs = tuple(dir for dir in _judge_dirs if os.path.isdir(dir))


def get_problem_root(pid):
    for dir in _judge_dirs:
        path = os.path.join(dir, pid)
        if os.path.exists(path):
            return path
    return None


def get_problem_roots():
    return _judge_dirs


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
