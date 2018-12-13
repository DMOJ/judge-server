import os
import subprocess
import zipfile
from functools import partial

import six
import yaml
from yaml.parser import ParserError
from yaml.scanner import ScannerError

from dmoj import checkers
from dmoj.config import InvalidInitException, ConfigNode
from dmoj.error import InternalError
from dmoj.generator import GeneratorManager
from dmoj.judgeenv import env, get_problem_root
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
                'symlinks': {},
            })
        except (IOError, KeyError, ParserError, ScannerError) as e:
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
        base = get_problem_root(self.problem_id)
        try:
            return open(os.path.join(base, key), 'rb').read()
        except IOError:
            if self.archive:
                zipinfo = self.archive.getinfo(key)
                return self.archive.open(zipinfo).read()
            raise KeyError('file "%s" could not be found in "%s"' % (key, base))

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
        self.has_binary_data = config.binary_data
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
            if isinstance(mapping.fd, six.string_types):
                mapped = {'stdin': 0, 'stdout': 1, 'stderr': 2}.get(mapping.fd, None)
                if mapped is None:
                    raise InvalidInitException("unknown named fd for redirect '%s'" % redirect)
                mapping.fd = mapped

            filtered_data[redirect] = (mapping.mode, mapping.fd)

        return filtered_data

    def _normalize(self, data):
        # Perhaps the correct answer may be "no output", in which case it'll be None here if
        # sourced from a generator
        data = data or b''
        # Normalize all newline formats (\r\n, \r, \n) to \n, otherwise we have problems with people creating
        # data on Macs (\r newline) when judged programs assume \n
        if self.has_binary_data:
            return data
        return data.replace(b'\r\n', b'\r').replace(b'\r', b'\n')

    def _run_generator(self, gen, args=None):
        flags = []
        args = args or []

        # resource limits on how to run the generator
        time_limit = env.generator_time_limit
        memory_limit = env.generator_memory_limit
        use_sandbox = env.generator_sandboxing

        base = get_problem_root(self.problem.id)
        if isinstance(gen, six.string_types):
            filename = os.path.join(base, gen)
        else:
            filename = os.path.join(base, gen.source)
            if gen.flags:
                flags += gen.flags
            if not args and gen.args:
                args += gen.args

            time_limit = gen.time_limit or time_limit
            memory_limit = gen.memory_limit or memory_limit

            # Optionally allow disabling the sandbox
            if gen.use_sandbox is not None:
                use_sandbox = gen.use_sandbox

        executor = self.problem.generator_manager.get_generator(filename, flags)

        # convert all args to str before launching; allows for smoother int passing
        args = map(str, args)

        # we allow both "trusted" and "untrusted" generators, for different scenarios:
        # e.g., an untrusted generator may be one generated via site-managed data by an
        # arbitrary user, who shouldn't be allowed to do arbitrary things on the host machine
        if use_sandbox:
            # setting large buffers is really important, because otherwise stderr is unbuffered
            # and the generator begins calling into cptbox Python code really frequently
            proc = executor.launch(*args, time=time_limit, memory=memory_limit, pipe_stderr=True,
                                   stderr_buffer_size=65536, stdout_buffer_size=65536)
        else:
            proc = executor.launch_unsafe(*args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE)

        try:
            input = self.problem.problem_data[self.config['in']] if self.config['in'] else None
        except KeyError:
            input = None
        self._generated = list(map(self._normalize, proc.communicate(input)))

        if hasattr(proc, 'tle') and proc.tle:
            raise InternalError('generator timed out (> %s seconds)' % time_limit)
        if hasattr(proc, 'mle') and proc.mle:
            raise InternalError('generator ran out of memory (> %s Kb)' % memory_limit)
        if hasattr(proc, 'protection_fault') and proc.protection_fault:
            syscall, callname, args = proc.protection_fault
            raise InternalError('generator invoked disallowed syscall %s (%s)' % (syscall, callname))
        if proc.returncode:
            raise InternalError('generator exited with nonzero code: %s' % proc.returncode)

    def input_data(self):
        gen = self.config.generator

        # don't try running the generator if we specify an output file explicitly,
        # otherwise generator may segfault and we end up returning the output file anyway
        if gen and (not self.config['out'] or not self.config['in']):
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
            raise InvalidInitException('error loading checker: ' + str(e))
        if not hasattr(checker, 'check') or not callable(checker.check):
            raise InvalidInitException('malformed checker: no check method found')

        return partial(checker.check, **params)

    def free_data(self):
        self._generated = None

    def __str__(self):
        return 'TestCase{in=%s,out=%s,points=%s}' % (self.config['in'], self.config['out'], self.config['points'])
