from functools import partial
import os
import zipfile
import copy
import cStringIO

import yaml
from yaml.parser import ParserError
from yaml.scanner import ScannerError

import checkers
from judgeenv import get_problem_root
from utils.module import load_module, load_module_from_file


class InvalidInitException(Exception):
    """
    Your init.yml is bad and you should feel bad.
    """

    def __init__(self, message):
        super(InvalidInitException, self).__init__(message)


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
            dynamic_key = item + '+'
            if dynamic_key in self.raw_config:
                # Wrap in a ConfigNode so dynamic keys can benefit from the nice features of ConfigNode
                local = {'node': ConfigNode(self.raw_config.get(item, {}), self)}
                try:
                    exec self.raw_config[dynamic_key] in local
                except Exception as e:
                    import traceback

                    traceback.print_exc()
                    raise InvalidInitException('exception executing dynamic key ' + dynamic_key + ': ' + e.message)
                cfg = local['node']
                del self.raw_config[dynamic_key]
                self.raw_config[item] = cfg
            else:
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


class TestCase(object):
    def __init__(self, count, config, problem):
        self.position = count
        self.config = config
        self.problem = problem
        self.points = config.points
        self.output_prefix_length = config.output_prefix_length

    def _normalize(self, data):
        return data.replace('\r\n', '\n')

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
        return self._normalize(_in)

    def output_data(self):
        return self._normalize(self.problem.problem_data[self.config.out])

    def checker(self):
        try:
            name = self.config['checker'] or 'standard'
            if isinstance(name, ConfigNode):
                # TODO: remove legacy 'parameters'
                params = name['args'] or name['parameters'] or {}
                name = name['name']
            else:
                params = {}
            if '.' in name:
                try:
                    modname, ext = os.path.splitext(name)
                    checker = load_module_from_file(os.path.join(get_problem_root(self.problem.id), name))
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
        if any(isinstance(case, BatchedTestCase) for case in self.batched_cases):
            raise InvalidInitException("nested batches")
        self.problem = problem

    def __str__(self):
        return 'BatchedTestCase{cases=%s}' % str(self.batched_cases)


class _iofile_fetcher(dict):
    def __init__(self, problem_id, **kwargs):
        super(_iofile_fetcher, self).__init__(**kwargs)
        self.problem_id = problem_id

    def __missing__(self, key):
        return open(os.path.join(get_problem_root(self.problem_id), key), 'r').read()


class Problem(object):
    def __init__(self, problem_id, time_limit, memory_limit):
        self.id = problem_id
        self.time_limit = time_limit
        self.memory_limit = memory_limit

        self.problem_data = _iofile_fetcher(problem_id)
        self._testcase_counter = 0

        try:
            self.config = ConfigNode(yaml.safe_load(self.problem_data['init.yml']), defaults={
                'output_prefix_length': 64
            })
        except (IOError, ParserError, ScannerError) as e:
            raise InvalidInitException(str(e))

        self.problem_data.update(self._resolve_archive_files())
        self.cases = self._resolve_testcases(self.config['test_cases'])

    def _resolve_archive_files(self):
        files = dict()

        if self.config.archive:
            archive_path = os.path.join(get_problem_root(self.id), self.config.archive)
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
                cases.append(BatchedTestCase(case_config, self))
            else:
                cases.append(TestCase(self._testcase_counter, case_config, self))
        self._testcase_counter += 1
        return cases


def _generate_data(src, flags, argv, input_feed):
    pass

