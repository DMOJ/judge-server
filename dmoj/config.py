import copy
import os
import subprocess
import zipfile
from functools import partial

import yaml
from yaml.parser import ParserError
from yaml.scanner import ScannerError

from dmoj import checkers
from dmoj.generator import GeneratorManager
from dmoj.judgeenv import get_problem_root
from dmoj.utils.module import load_module_from_file


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
        if defaults:
            self.raw_config = defaults
            self.raw_config.update(raw_config)
        else:
            self.raw_config = raw_config
        self.parent = parent

    def __getattr__(self, item):
        return self[item]

    def __getitem__(self, item):
        try:
            def run_dynamic_key(dynamic_key, run_func):
                # Wrap in a ConfigNode so dynamic keys can benefit from the nice features of ConfigNode
                local = {'node': ConfigNode(self.raw_config.get(item, {}), self)}
                try:
                    cfg = run_func(self.raw_config[dynamic_key], local)
                except Exception as e:
                    import traceback

                    traceback.print_exc()
                    raise InvalidInitException('exception executing dynamic key ' + str(dynamic_key) + ': ' + e.message)
                del self.raw_config[dynamic_key]
                self.raw_config[item] = cfg

            if item + '++' in self.raw_config:
                def full(code, local):
                    exec code in local
                    return local['node']

                run_dynamic_key(item + '++', full)
            elif item + '+' in self.raw_config:
                run_dynamic_key(item + '+', lambda code, local: eval(code, local))
            cfg = self.raw_config[item]

            if isinstance(cfg, list) or isinstance(cfg, dict):
                cfg = ConfigNode(cfg, self)
        except (KeyError, IndexError, TypeError):
            cfg = self.parent[item] if self.parent else None
        return cfg

    def keys(self):
        return self.raw_config.keys()

    def __iter__(self):
        for cfg in self.raw_config:
            if isinstance(cfg, list) or isinstance(cfg, dict):
                cfg = ConfigNode(cfg, self)
            yield cfg

    def __str__(self):
        return '<ConfigNode(%s)>' % str(self.raw_config)


class TestCase(object):
    def __init__(self, count, config, problem):
        self.position = count
        self.config = config
        self.problem = problem
        self.points = config.points
        self.output_prefix_length = config.output_prefix_length
        self._generated = None

    def _normalize(self, data):
        return data.replace('\r\n', '\n')

    def _run_generator(self, gen, args=None):
        flags = []
        args = args or []
        if isinstance(gen, str):
            filename = os.path.join(get_problem_root(self.problem.id), gen)
        else:
            filename = gen.source
            if gen.flags:
                flags += gen.flags
            if not args and gen.args:
                args += gen.args

        executor = self.problem.generator_manager.get_generator(filename, flags)
        # convert all args to str before launching; allows for smoother int passing
        proc = executor.launch_unsafe(*map(str, args), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        try:
            input = self.problem.problem_data[self.config['in']] if self.config['in'] else None
        except KeyError:
            input = None
        self._generated = map(self._normalize, proc.communicate(input))

    def input_data(self):
        gen = self.config.generator
        if gen:
            if self._generated is None:
                self._run_generator(gen, args=self.config.generator_args)
            if self._generated[0]:
                return self._generated[0]
        # in file is optional
        return self._normalize(self.problem.problem_data[self.config['in']]) if self.config['in'] else ''

    def output_data(self):
        if self.config.out:
            return self._normalize(self.problem.problem_data[self.config.out])
        gen = self.config.generator
        if gen:
            if self._generated is None:
                self._run_generator(gen, args=self.config.generator_args)
            return self._generated[1]

    def checker(self):
        try:
            name = self.config['checker'] or 'standard'
            if isinstance(name, ConfigNode):
                params = name['args'] or {}
                name = name['name']
            else:
                params = {}
            if '.' in name:
                try:
                    checker = self.problem.load_checker(name)
                except IOError:
                    raise InvalidInitException('checker module path does not exist: %s' % name)
            else:
                checker = getattr(checkers, name)
        except AttributeError as e:
            raise InvalidInitException('error loading checker: ' + e.message)
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


class ProblemDataManager(dict):
    def __init__(self, problem_id, **kwargs):
        super(ProblemDataManager, self).__init__(**kwargs)
        self.problem_id = problem_id
        self.archive = None

    def __missing__(self, key):
        try:
            return open(os.path.join(get_problem_root(self.problem_id), key), 'r').read()
        except IOError:
            if self.archive:
                zipinfo = self.archive.getinfo(key)
                return self.archive.open(zipinfo).read()
            raise KeyError()

    def __del__(self):
        if self.archive:
            self.archive.close()


class Problem(object):
    def __init__(self, problem_id, time_limit, memory_limit):
        self.id = problem_id
        self.time_limit = time_limit
        self.memory_limit = memory_limit
        self.generator_manager = GeneratorManager()

        self.problem_data = ProblemDataManager(problem_id)

        # Checkers modules must be stored in a dict, for the duration of execution,
        # lest globals be deleted with the module.
        self._checkers = {}
        self._testcase_counter = 0

        try:
            self.config = ConfigNode(yaml.safe_load(self.problem_data['init.yml']), defaults={
                'output_prefix_length': 64,
                'output_limit_length': 25165824,
            })
        except (IOError, ParserError, ScannerError) as e:
            raise InvalidInitException(str(e))

        self.problem_data.archive = self._resolve_archive_files()
        self.cases = self._resolve_testcases(self.config['test_cases'])

    def load_checker(self, name):
        if name in self._checkers:
            return self._checkers[name]
        self._checkers[name] = checker = load_module_from_file(os.path.join(get_problem_root(self.id), name))
        return checker

    def _resolve_archive_files(self):
        if self.config.archive:
            archive_path = os.path.join(get_problem_root(self.id), self.config.archive)
            if not os.path.exists(archive_path):
                raise InvalidInitException('archive file "%s" does not exist' % archive_path)
            try:
                archive = zipfile.ZipFile(archive_path, 'r')
            except zipfile.BadZipfile:
                raise InvalidInitException('bad archive: "%s"' % archive_path)
            return archive
        return None

    def _resolve_testcases(self, cfg):
        cases = []
        for case_config in cfg:
            if 'batched' in case_config.raw_config:
                cases.append(BatchedTestCase(case_config, self))
            else:
                cases.append(TestCase(self._testcase_counter, case_config, self))
        self._testcase_counter += 1
        return cases
