import argparse
import os
import ssl
from typing import List, Set

import yaml

from dmoj.config import ConfigNode
# noinspection PyUnresolvedReferences
from dmoj.utils import pyyaml_patch  # noqa: F401, imported for side effect
from dmoj.utils.unicode import utf8text

problem_dirs = ()
problem_watches = ()
env = ConfigNode(defaults={
    'selftest_time_limit': 10,  # 10 seconds
    'selftest_memory_limit': 131072,  # 128mb of RAM
    'generator_compiler_time_limit': 30,  # 30 seconds
    'generator_time_limit': 20,  # 20 seconds
    'generator_memory_limit': 524288,  # 512mb of RAM
    'compiler_time_limit': 10,  # Kill compiler after 10 seconds
    'compiler_size_limit': 131072,  # Maximum allowable compiled file size, 128mb
    'compiler_output_character_limit': 65536,  # Number of characters allowed in compile output
    'compiled_binary_cache_dir': None,  # Location to store cached binaries, defaults to tempdir
    'compiled_binary_cache_size': 100,  # Maximum number of executables to cache (LRU order)
    'runtime': {},
    # Map of executor: [list of extra allowed file regexes], used to configure
    # the filesystem sandbox on a per-machine basis, without having to hack
    # executor source.
    'extra_fs': {},
    # List of judge URLs to ping on problem data updates (the URLs are expected
    # to host judges running with --api-host and --api-port)
    'update_pings': [],
    # Directory to use as temporary submission storage, system default
    # (e.g. /tmp) if left blank.
    'tempdir': None,
}, dynamic=False)
_root = os.path.dirname(__file__)

log_file = server_host = server_port = no_ansi = no_watchdog = problem_regex = case_regex = None
secure = no_cert_check = False
cert_store = api_listen = None

startup_warnings: List[str] = []
cli_command: List[str] = []

only_executors: Set[str] = set()
exclude_executors: Set[str] = set()


def load_env(cli=False, testsuite=False):  # pragma: no cover
    global problem_dirs, only_executors, exclude_executors, log_file, server_host, \
        server_port, no_ansi, no_ansi_emu, env, startup_warnings, no_watchdog, \
        problem_regex, case_regex, api_listen, secure, no_cert_check, cert_store, \
        problem_watches, cli_command

    if cli:
        description = 'Starts a shell for interfacing with a local judge instance.'
    else:
        description = 'Spawns a judge for a submission server.'

    parser = argparse.ArgumentParser(description=description)
    if not cli:
        parser.add_argument('server_host', help='host to connect for the server')
        parser.add_argument('judge_name', nargs='?', help='judge name (overrides configuration)')
        parser.add_argument('judge_key', nargs='?', help='judge key (overrides configuration)')
        parser.add_argument('-p', '--server-port', type=int, default=9999,
                            help='port to connect for the server')
    else:
        parser.add_argument('command', nargs='*', help='invoke CLI command without spawning shell')

    parser.add_argument('-c', '--config', type=str, default='~/.dmojrc',
                        help='file to load judge configurations from (default: ~/.dmojrc)')

    if not cli:
        parser.add_argument('-l', '--log-file',
                            help='log file to use')
        parser.add_argument('--no-watchdog', action='store_true',
                            help='disable use of watchdog on problem directories')
        parser.add_argument('-a', '--api-port', type=int, default=None,
                            help='port to listen for the judge API (do not expose to public, '
                                 'security is left as an exercise for the reverse proxy)')
        parser.add_argument('-A', '--api-host', default='127.0.0.1',
                            help='IPv4 address to listen for judge API')

        parser.add_argument('-s', '--secure', action='store_true',
                            help='connect to server via TLS')
        parser.add_argument('-k', '--no-certificate-check', action='store_true',
                            help='do not check TLS certificate')
        parser.add_argument('-T', '--trusted-certificates', default=None,
                            help='use trusted certificate file instead of system')

    _group = parser.add_mutually_exclusive_group()
    _group.add_argument('-e', '--only-executors',
                        help='only listed executors will be loaded (comma-separated)')
    _group.add_argument('-x', '--exclude-executors',
                        help='prevent listed executors from loading (comma-separated)')

    parser.add_argument('--no-ansi', action='store_true', help='disable ANSI output')

    if testsuite:
        parser.add_argument('tests_dir', help='directory where tests are stored')
        parser.add_argument('problem_regex', help='when specified, only matched problems will be tested', nargs='?')
        parser.add_argument('case_regex', help='when specified, only matched cases will be tested', nargs='?')

    args = parser.parse_args()

    server_host = getattr(args, 'server_host', None)
    server_port = getattr(args, 'server_port', None)
    cli_command = getattr(args, 'command', [])

    no_ansi = args.no_ansi
    no_watchdog = True if cli else args.no_watchdog
    if not cli:
        api_listen = (args.api_host, args.api_port) if args.api_port else None

        if ssl:
            secure = args.secure
            no_cert_check = args.no_certificate_check
            cert_store = args.trusted_certificates

    log_file = getattr(args, 'log_file', None)
    only_executors |= args.only_executors and set(args.only_executors.split(',')) or set()
    exclude_executors |= args.exclude_executors and set(args.exclude_executors.split(',')) or set()

    model_file = os.path.expanduser(args.config)

    with open(model_file) as init_file:
        env.update(yaml.safe_load(init_file))

        if getattr(args, 'judge_name', None):
            env['id'] = args.judge_name

        if getattr(args, 'judge_key', None):
            env['key'] = args.judge_key

        problem_dirs = env.problem_storage_root
        if problem_dirs is None:
            if not testsuite:
                raise SystemExit('problem_storage_root not specified in "%s"; '
                                 'no problems available to grade' % model_file)
        else:
            # Populate cache and send warnings
            get_problem_roots(warnings=True)

            def get_path(x, y):
                return utf8text(os.path.normpath(os.path.join(x, y)))

            problem_watches = []
            for dir in problem_dirs:
                if isinstance(dir, ConfigNode):
                    for _, recursive_root in dir.iteritems():
                        problem_watches.append(get_path(_root, recursive_root))
                else:
                    problem_watches.append(get_path(_root, dir))

    if testsuite:
        if not os.path.isdir(args.tests_dir):
            raise SystemExit('Invalid tests directory')
        problem_dirs = [args.tests_dir]
        clear_problem_dirs_cache()

        import re
        if args.problem_regex:
            try:
                problem_regex = re.compile(args.problem_regex)
            except re.error:
                raise SystemExit('Invalid problem regex')
        if args.case_regex:
            try:
                case_regex = re.compile(args.case_regex)
            except re.error:
                raise SystemExit('Invalid case regex')


def get_problem_root(pid):
    for dir in get_problem_roots():
        path = os.path.join(dir, pid)
        if os.path.exists(path):
            return path
    return None


_problem_dirs_cache = None


def get_problem_roots(warnings=False):
    global _problem_dirs_cache

    if _problem_dirs_cache is not None:
        return _problem_dirs_cache

    def get_path(x, y):
        return utf8text(os.path.normpath(os.path.join(x, y)))

    if isinstance(problem_dirs, list):
        _problem_dirs_cache = problem_dirs
        return problem_dirs
    elif isinstance(problem_dirs, ConfigNode):
        def find_directories_by_depth(dir, depth):
            if depth < 0:
                raise ValueError('negative depth reached')
            if not depth:
                if os.path.isdir(dir):
                    return [dir]
                else:
                    return []
            ret = []
            for child in os.listdir(dir):
                next = os.path.join(dir, child)
                if os.path.isdir(next):
                    ret += find_directories_by_depth(next, depth - 1)
            return ret

        dirs = []
        for dir in problem_dirs:
            if isinstance(dir, ConfigNode):
                for depth, recursive_root in dir.iteritems():
                    try:
                        dirs += find_directories_by_depth(get_path(_root, recursive_root), int(depth))
                    except ValueError:
                        startup_warnings.append('illegal depth argument %s' % depth)
            else:
                dirs.append(get_path(_root, dir))
    else:
        dirs = os.path.join(_root, problem_dirs)
        dirs = [get_path(dirs, dir) for dir in os.listdir(dirs)]
        dirs = [dir for dir in dirs if os.path.isdir(dir)]

    if warnings:
        cleaned_dirs = []
        for dir in dirs:
            if not os.path.exists(dir) or not os.path.isdir(dir):
                startup_warnings.append('cannot access problem directory %s (does it exist?)' % dir)
                continue
            cleaned_dirs.append(dir)
    else:
        cleaned_dirs = dirs
    _problem_dirs_cache = cleaned_dirs
    return cleaned_dirs


def clear_problem_dirs_cache():
    global _problem_dirs_cache
    _problem_dirs_cache = None


def get_problem_watches():
    return problem_watches


def get_supported_problems():
    """
    Fetches a list of all problems supported by this judge.
    :return:
        A list of all problems in tuple format: (problem id, mtime)
    """
    problems = []
    for dir in get_problem_roots():
        for problem in os.listdir(dir):
            problem = utf8text(problem)
            if os.access(os.path.join(dir, problem, 'init.yml'), os.R_OK):
                problems.append((problem, os.path.getmtime(os.path.join(dir, problem))))
    return problems


def get_runtime_versions():
    from dmoj.executors import executors
    return {name: clazz.Executor.get_runtime_versions() for name, clazz in executors.items()}
