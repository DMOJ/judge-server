import os
import subprocess
import zipfile
from functools import partial

import yaml
from yaml.parser import ParserError
from yaml.scanner import ScannerError

from dmoj import checkers
from dmoj.config import InvalidInitException, ConfigNode
from dmoj.generator import GeneratorManager
from dmoj.judgeenv import get_problem_root
from dmoj.utils.module import load_module_from_file


class Problem(object):
    def __init__(self, problem_id, time_limit, memory_limit, load_pretests_only=False):
        self.id = problem_id
        self.time_limit = time_limit
        self.memory_limit = memory_limit
        self.generator_manager = GeneratorManager()

        self.problem_data = ProblemDataManager(problem_id)

        # Checkers modules must be stored in a dict, for the duration of execution,
        # lest globals be deleted with the module.
        self._checkers = {}
        self._testcase_counter = 0
        self._batch_counter = 0

        try:
            doc = yaml.safe_load(self.problem_data['init.yml'])
            if not doc:
                raise InvalidInitException('I find your lack of content disturbing.')
            self.config = ConfigNode(doc, defaults={
                'wall_time_factor': 3,
                'output_prefix_length': 64,
                'output_limit_length': 25165824,
                'binary_data': False,
                'short_circuit': True,
            })
        except (IOError, ParserError, ScannerError) as e:
            raise InvalidInitException(str(e))

        self.problem_data.archive = self._resolve_archive_files()

        self.is_pretested = load_pretests_only and 'pretest_test_cases' in self.config
        self.cases = self._resolve_testcases(self.config['pretest_test_cases' if self.is_pretested else 'test_cases'])

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

    def _resolve_testcases(self, cfg, batch_no=0):
        cases = []
        for case_config in cfg:
            if 'batched' in case_config.raw_config:
                self._batch_counter += 1
                cases.append(BatchedTestCase(self._batch_counter, case_config, self))
            else:
                cases.append(TestCase(self._testcase_counter, batch_no, case_config, self))
                self._testcase_counter += 1
        return cases


class ProblemDataManager(dict):
    def __init__(self, problem_id, **kwargs):
        super(ProblemDataManager, self).__init__(**kwargs)
        self.problem_id = problem_id
        self.archive = None

    def __missing__(self, key):
        try:
            return open(os.path.join(get_problem_root(self.problem_id), key), 'rb').read()
        except IOError:
            if self.archive:
                zipinfo = self.archive.getinfo(key)
                return self.archive.open(zipinfo).read()
            raise KeyError('file "%s" could not be found' % key)

    def __del__(self):
        if self.archive:
            self.archive.close()


class BatchedTestCase(object):
    def __init__(self, batch_no, config, problem):
        self.config = config
        self.batch_no = batch_no
        self.points = config.points
        self.batched_cases = problem._resolve_testcases(config['batched'], batch_no=batch_no)
        if any(isinstance(case, BatchedTestCase) for case in self.batched_cases):
            raise InvalidInitException("nested batches")
        self.problem = problem

    def __str__(self):
        return 'BatchedTestCase{cases=%s}' % str(self.batched_cases)


class TestCase(object):
    def __init__(self, count, batch_no, config, problem):
        self.position = count
        self.batch = batch_no
        self.config = config
        self.problem = problem
        self.points = config.points
        self.output_prefix_length = config.output_prefix_length
        self._generated = None

    def io_redirects(self):
        redirects = self.config.io_redirects
        if not redirects:
            return None

        # io_redirects:
        #   DATA01.in:
        #     fd: 0
        #     mode: "r"
        #   DATA01.out:
        #     fd: 1
        #     mode: "w"

        filtered_data = {}

        for redirect in redirects:
            mapping = redirects[redirect]
            if 'fd' not in mapping:
                raise InvalidInitException("no fd specified for redirect '%s'" % redirect)
            if 'mode' not in mapping:
                raise InvalidInitException("no mode specified for redirect '%s'" % redirect)
            if mapping.mode not in 'rw':
                raise InvalidInitException("invalid mode for redirect '%s': valid options are 'r', 'w'" % redirect)
            if isinstance(mapping.fd, str):
                mapped = {'stdin': 0, 'stdout': 1, 'stderr': 2}.get(mapping.fd, None)
                if mapped is None:
                    raise InvalidInitException("unknown named fd for redirect '%s'" % redirect)
                mapping.fd = mapped

            filtered_data[redirect] = (mapping.mode, mapping.fd)

        return filtered_data

    def _normalize(self, data):
        # Normalize all newline formats (\r\n, \r, \n) to \n, otherwise we have problems with people creating
        # data on Macs (\r newline) when judged programs assume \n
        if self.config.binary_data:
            return data
        return data.replace('\r\n', '\r').replace('\r', '\n')

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
        proc = executor.launch_unsafe(*map(str, args), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)

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

    def free_data(self):
        self._generated = None

    def __str__(self):
        return 'TestCase{in=%s,out=%s,points=%s}' % (self.config['in'], self.config['out'], self.config['points'])
