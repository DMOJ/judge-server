import argparse
import json
import os
import sys

try:
    import yaml
except ImportError:
    yaml = None


__all__ = ['env', 'get_problem_root', 'get_problem_roots']

_judge_dirs = ()
env = {}
_root = os.path.dirname(__file__)
fs_encoding = os.environ.get('DMOJ_ENCODING', sys.getfilesystemencoding())


def unicodify(string):
    if isinstance(string, str):
        return string.decode(fs_encoding)
    return string


def _get_default_model_file():
    model_file = os.path.join(os.path.dirname(__file__), 'data', 'judge', 'judge.yml')
    if os.path.exists(model_file):
        if yaml is None:
            print>>sys.stderr, 'Warning: found judge.yml but no yaml parser'
        else:
            return model_file
    model_file = os.path.join(os.path.dirname(__file__), 'data', 'judge', 'judge.json')
    return model_file


_parser = argparse.ArgumentParser(description='''
    Spawns a judge for a submission server.
''')
_parser.add_argument('server_host', nargs='?',
                     help='host to listen for the server')
_parser.add_argument('-p', '--server-port', type=int, default=9999,
                     help='port to listen for the server')
_parser.add_argument('-c', '--config', type=str, default=None,
                     help='file to load judge configurations from')
_args = _parser.parse_args()

server_host = _args.server_host
server_port = _args.server_port

model_file = _args.config
if model_file is None:
    model_file = _get_default_model_file()
    print>>sys.stderr, 'Warning: using default judge model path (%s) use --config to specify path' % model_file

with open(model_file) as init_file:
    if model_file.endswith('.json'):
        env = json.load(init_file)
    elif model_file.endswith(('.yml', '.yaml')):
        env = yaml.safe_load(init_file)
    else:
        raise ValueError('Unknown judge model path')
    dirs = env.get('problem_storage_root', os.path.join('data', 'problems'))
    if isinstance(dirs, list):
        _judge_dirs = tuple(unicodify(os.path.normpath(os.path.join(_root, dir))) for dir in dirs)
    else:
        _judge_dirs = unicodify(os.path.normpath(os.path.join(_root, dirs)))


def get_problem_root(pid):
    for dir in _judge_dirs:
        path = os.path.join(dir, pid)
        if os.path.exists(path):
            return path
    return None


def get_problem_roots():
    return _judge_dirs