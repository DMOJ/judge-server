import argparse
import os
import sys

import yaml

from dmoj.config import ConfigNode

try:
    import ssl
except ImportError:
    ssl = None

problem_dirs = ()
env = ConfigNode(defaults={
    'selftest_sandboxing': True,
    'runtime': {},
}, dynamic=False)
_root = os.path.dirname(__file__)
fs_encoding = os.environ.get('DMOJ_ENCODING', sys.getfilesystemencoding())

log_file = server_host = server_port = no_ansi = no_ansi_emu = no_watchdog = problem_regex = case_regex = None
secure = no_cert_check = False
cert_store = api_listen = None

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
        problem_regex, case_regex, api_listen, secure, no_cert_check, cert_store
    parser = argparse.ArgumentParser(description='''
        Spawns a judge for a submission server.
    ''')
    if not cli:
        parser.add_argument('server_host', help='host to connect for the server')
        parser.add_argument('judge_name', nargs='?', help='judge name (overrides configuration)')
        parser.add_argument('judge_key', nargs='?', help='judge key (overrides configuration)')
        parser.add_argument('-p', '--server-port', type=int, default=9999,
                            help='port to connect for the server')
    parser.add_argument('-c', '--config', type=str, default=None, required=True,
                        help='file to load judge configurations from')

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

        if ssl:
            parser.add_argument('-s', '--secure', action='store_true',
                                help='connect to server via TLS')
            parser.add_argument('-k', '--no-certificate-check', action='store_true',
                                help='do not check TLS certificate')
            parser.add_argument('-T', '--trusted-certificates', default=None,
                                help='use trusted certificate file instead of system')
        else:
            parser.set_defaults(secure=False, no_certificate_check=False, trusted_certificates=None)

    _group = parser.add_mutually_exclusive_group()
    _group.add_argument('-e', '--only-executors',
                        help='only listed executors will be loaded (comma-separated)')
    _group.add_argument('-x', '--exclude-executors',
                        help='prevent listed executors from loading (comma-separated)')

    parser.add_argument('--no-ansi', action='store_true', help='disable ANSI output')
    if os.name == 'nt':
        parser.add_argument('--no-ansi-emu', action='store_true', help='disable ANSI emulation on Windows')

    if testsuite:
        parser.add_argument('tests_dir', help='directory where tests are stored')
        parser.add_argument('problem_regex', help='when specified, only matched problems will be tested', nargs='?')
        parser.add_argument('case_regex', help='when specified, only matched cases will be tested', nargs='?')

    args = parser.parse_args()

    server_host = getattr(args, 'server_host', None)
    server_port = getattr(args, 'server_port', None)

    no_ansi_emu = args.no_ansi_emu if os.name == 'nt' else True
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

    model_file = args.config

    with open(model_file) as init_file:
        env.update(yaml.safe_load(init_file))

        if getattr(args, 'judge_name', None):
            env['id'] = args.judge_name

        if getattr(args, 'judge_key', None):
            env['key'] = args.judge_key

        dirs = env.problem_storage_root
        if dirs is not None:
            get_path = lambda x, y: unicodify(os.path.normpath(os.path.join(x, y)))
            if isinstance(dirs, ConfigNode):

                def find_directories_by_depth(dir, depth):
                    if depth < 0: raise ValueError('negative depth reached')
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

                problem_dirs = []
                for dir in dirs:
                    if isinstance(dir, ConfigNode):
                        for depth, recursive_root in dir.iteritems():
                            try:
                                problem_dirs += find_directories_by_depth(get_path(_root, recursive_root), int(depth))
                            except ValueError:
                                startup_warnings.append('illegal depth arguement %s' % depth)
                    else:
                        problem_dirs.append(get_path(_root, dir))
                problem_dirs = tuple(problem_dirs)
            else:
                problem_dirs = os.path.join(_root, dirs)
                problem_dirs = [get_path(problem_dirs, dir) for dir in os.listdir(problem_dirs)]
                problem_dirs = tuple(dir for dir in problem_dirs if os.path.isdir(dir))

            cleaned_dirs = []
            for dir in problem_dirs:
                if not os.path.exists(dir) or not os.path.isdir(dir):
                    startup_warnings.append('cannot access problem directory %s (does it exist?)' % dir)
                    continue
                cleaned_dirs.append(dir)
            problem_dirs = cleaned_dirs

    if testsuite:
        if not os.path.isdir(args.tests_dir):
            raise SystemExit('Invalid tests directory')
        problem_dirs = [args.tests_dir]

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
