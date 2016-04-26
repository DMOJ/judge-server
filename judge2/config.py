from functools import partial
import os
import zipfile
import imp
import yaml
import copy
import checkers
from judgeenv import get_problem_root


class InvalidInitException(Exception):
    """
    Your init.yml is bad and you should feel bad.
    """
    pass


class ConfigNode(object):
    """
    A wrapper around a YAML configuration object for easier use.

    Consider the following YAML object, stored in a ConfigNode "node":

    output_prefix_length: 5
    test_cases: [
        {
            batched: [
                {
                    in: ruby.1.in
                },
                {
                    in: ruby.2.in,
                    output_prefix_length: 0,
                }
            ],
            out: ruby.out,
            points: 10
        },
        {
            in: ruby.4.in,
            out: ruby.4.out,
            points: 15
        }
    ]

    node.test_cases[0].batched[0]['in'] == 'ruby.1.in'
    node.test_cases[0].batched[0].out == 'ruby.out'
    node.test_cases[0].batched[0].points == 10
    node.test_cases[1].points == 15
    node.test_cases[1].output_prefix_length == 5
    node.test_cases[0].batched[0].output_prefix_length == 5
    node.test_cases[0].batched[1].output_prefix_length == 0
    """

    def __init__(self, raw_config, parent=None, defaults=None):
        self.raw_config = copy.deepcopy(raw_config)
        if defaults:
            self.raw_config.update(defaults)
        self.parent = parent

    def __getattr__(self, item):
        return self[item]

    def __getitem__(self, item):
        try:
            cfg = self.raw_config[item]
            if isinstance(cfg, list) or isinstance(cfg, dict):
                cfg = ConfigNode(cfg, self)
        except (KeyError, IndexError, TypeError):
            cfg = self.parent[item] if self.parent else None
        return cfg

    def __iter__(self):
        for cfg in self.raw_config:
            if isinstance(cfg, list) or isinstance(cfg, dict):
                cfg = ConfigNode(cfg, self)
            yield cfg

    def __str__(self):
        return str(self.raw_config)


class _iofile_fetcher(dict):
    def __init__(self, problem_id, **kwargs):
        super(_iofile_fetcher, self).__init__(**kwargs)
        self.problem_id = problem_id

    def __missing__(self, key):
        return open(os.path.join(get_problem_root(self.problem_id), key), 'r')


class Problem(object):
    class TestCase(object):
        def __init__(self, config, problem):
            self.config = config
            self.problem = problem
            self.points = config.points
            self.output_prefix_length = config.output_prefix_length

        def input_data(self):
            _in = self.problem.problem_data[self.config['in']]

            gen = self.config.generator
            if gen:
                flags = []  # default flags
                args = []  # default args - maybe pass WINDOWS_JUDGE or LINUX_JUDGE
                if isinstance(gen, str):
                    source = gen
                else:
                    source = gen.source
                    if gen.flags:
                        flags += gen.flags
                    if gen.args:
                        args += gen.args
                return _generate_data(source, flags, self.config.generator_args or args, _in)
            return _in

        def output_data(self):
            return self.problem.problem_data[self.config.out]

        def checker(self):
            try:
                name = self.config.get('checker', 'standard')
                if isinstance(name, dict):
                    params = name.get('args', {})
                    name = name['name']
                else:
                    params = {}
                if '.' in name:
                    try:
                        checker = load_module(os.path.splitext(os.path.split(name)[1])[0],
                                              self.problem.problem_data[name], name)
                    except IOError:
                        raise InvalidInitException('checker module path does not exist: %s' % name)
                else:
                    checker = getattr(checkers, name)
            except AttributeError:
                raise InvalidInitException('error loading checker')
            if not hasattr(checker, 'check') or not callable(checker.check):
                raise InvalidInitException('malformed checker: no check method found')

            return partial(checker.check, **params)

        def __str__(self):
            return 'TestCase{in=%s,out=%s,points=%s}' % (self.config['in'], self.config['out'], self.config['points'])

    class BatchedTestCase(object):
        def __init__(self, config, problem):
            self.config = config
            self.batched_cases = problem._resolve_testcases(config['batched'])
            if any(isinstance(case, Problem.BatchedTestCase) for case in self.batched_cases):
                raise InvalidInitException("nested batches")
            self.problem = problem

        def __str__(self):
            return 'BatchedTestCase{cases=%s}' % str(self.batched_cases)

    def __init__(self, problem_id):
        self.problem_id = problem_id

        self.problem_data = _iofile_fetcher(problem_id)

        self.config = ConfigNode(yaml.load(self.problem_data['init2.yml']), defaults={
            'output_prefix_length': 64
        })

        self.problem_data.update(self._resolve_archive_files())
        self.cases = self._resolve_testcases(self.config['test_cases'])

    def _resolve_archive_files(self):
        files = dict()

        if self.config.archive:
            archive_path = os.path.join(get_problem_root(self.problem_id), self.config.archive)
            if not os.path.exists(archive_path):
                raise InvalidInitException('archive file "%s" does not exist' % archive_path)
            try:
                archive = zipfile.ZipFile(archive_path, 'r')
            except zipfile.BadZipfile:
                raise InvalidInitException('bad archive: "%s"' % archive_path)
            try:
                for name in archive.infolist():
                    files[name.filename] = archive.read(name)
            finally:
                archive.close()

        return files

    def _resolve_testcases(self, cfg):
        cases = []
        for case_config in cfg:
            if 'batched' in case_config.raw_config:
                cases.append(Problem.BatchedTestCase(case_config, self))
            else:
                cases.append(Problem.TestCase(case_config, self))
        return cases


def load_module(name, code, filename=None):
    mod = imp.new_module(name)
    if filename is not None:
        mod.__file__ = filename
    exec compile(code, filename or '<string>', 'exec') in mod.__dict__
    return mod


def _generate_data(src, flags, argv, input_feed):
    pass


problem = Problem('dmpg15s5')
case = problem.cases[0].batched_cases[0]
print case.input_data()
print case.points
print case.output_prefix_length