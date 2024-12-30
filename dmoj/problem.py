import itertools
import os
import re
import shutil
import subprocess
import zipfile
from collections import defaultdict
from functools import partial
from typing import (
    DefaultDict,
    Dict,
    Iterable,
    Iterator,
    List,
    Match,
    Optional,
    Pattern,
    Set,
    TYPE_CHECKING,
    Tuple,
    Type,
    Union,
    cast,
)

import yaml
from yaml.parser import ParserError
from yaml.scanner import ScannerError

from dmoj import checkers
from dmoj.checkers import Checker
from dmoj.config import ConfigNode, InvalidInitException
from dmoj.cptbox.utils import MemoryIO, MmapableIO
from dmoj.judgeenv import env, get_problem_root
from dmoj.utils.helper_files import compile_with_auxiliary_files, parse_helper_file_error
from dmoj.utils.module import load_module_from_file
from dmoj.utils.normalize import normalized_file_copy

if TYPE_CHECKING:
    from dmoj.graders.base import BaseGrader

DEFAULT_TEST_CASE_INPUT_PATTERN = r'^(?=.*?\.in|in).*?(?:(?:^|\W)(?P<batch>\d+)[^\d\s]+)?(?P<case>\d+)[^\d\s]*$'
DEFAULT_TEST_CASE_OUTPUT_PATTERN = r'^(?=.*?\.out|out).*?(?:(?:^|\W)(?P<batch>\d+)[^\d\s]+)?(?P<case>\d+)[^\d\s]*$'


class BaseTestCase:
    config: ConfigNode
    points: int
    problem: 'Problem'


class Problem:
    id: str
    time_limit: float
    memory_limit: int
    meta: ConfigNode
    root_dir: str
    _checkers: Dict[str, Checker]
    problem_data: 'ProblemDataManager'
    config: 'ProblemConfig'

    def __init__(self, problem_id: str, time_limit: float, memory_limit: int, meta: dict) -> None:
        self.id = problem_id
        self.time_limit = time_limit
        self.memory_limit = memory_limit
        self.meta = ConfigNode(meta)
        self.run_pretests_only = self.meta.pretests_only
        self._batch_counter = 0
        self._testcase_counter = 0

        # Cache root dir so that we don't need to scan all roots (potentially very slow on networked mount).
        root_dir = get_problem_root(problem_id)
        assert root_dir is not None
        self.root_dir = root_dir
        self.problem_data = ProblemDataManager(self.root_dir)

        # Checkers modules must be stored in a dict, for the duration of execution,
        # lest globals be deleted with the module.
        self._checkers = {}

        self.config = ProblemConfig(self.problem_data, meta)

        self.problem_data.archive = self._resolve_archive_files()

        if not self._resolve_test_cases():
            raise InvalidInitException('No test cases? What am I judging?')

    def _match_test_cases(
        self,
        filenames: List[str],
        input_case_pattern: Pattern[str],
        output_case_pattern: Pattern[str],
        case_points: Iterator[int],
    ) -> List[dict]:
        key_type = Union[str, int, None]

        def try_match_int(match: Match[str], group: str) -> key_type:
            try:
                val = match.group(group)
            except IndexError:
                return None

            try:
                return int(val)
            except (ValueError, TypeError):
                return val

        def parse_position(pattern: Pattern[str], filename: str) -> Optional[Tuple[key_type, key_type]]:
            match = pattern.match(filename)
            if not match:
                return None

            # Allow batches and case numbers to be alphanumeric, in which case we will sort them lexicographically.
            # Still attempt to process them as integers first, though, since most problems will use this format.
            return try_match_int(match, 'batch'), try_match_int(match, 'case')

        class _TestCase:
            input_file: Optional[str] = None
            output_file: Optional[str] = None

        # Match all cases with the same (batch, position) mapping.
        groups: DefaultDict[key_type, DefaultDict[key_type, _TestCase]] = defaultdict(lambda: defaultdict(_TestCase))
        batch_ids: Set[key_type] = set()

        for filetype, pattern in (('input_file', input_case_pattern), ('output_file', output_case_pattern)):
            for testcase_file in filenames:
                testcase_parse = parse_position(pattern, testcase_file)
                if testcase_parse is None:
                    continue

                batch, case = testcase_parse
                if case is None:
                    raise InvalidInitException('test case format yielded no case number')
                if batch is not None:
                    batch_ids.add(batch)
                else:
                    batch = case  # for non-batched cases, treat case number as batch number

                setattr(groups[batch][case], filetype, testcase_file)

        test_cases = []
        for batch_or_case_id in sorted(groups.keys(), key=lambda id: (isinstance(id, int), id)):
            group_cases = groups[batch_or_case_id]
            if batch_or_case_id in batch_ids:
                test_cases.append(
                    {
                        'batched': [
                            {'in': testcase.input_file, 'out': testcase.output_file}
                            for _, testcase in sorted(group_cases.items())
                        ],
                        'points': next(case_points),
                    }
                )
            else:
                if len(group_cases) > 1:
                    raise InvalidInitException('problem has conflicting test cases: %s' % group_cases)
                test_case = next(iter(group_cases.values()))
                test_cases.append(
                    {'in': test_case.input_file, 'out': test_case.output_file, 'points': next(case_points)}
                )

        return test_cases

    def _problem_file_list(self) -> List[str]:
        # We *could* support testcase format specifiers without an archive, but it's harder and most problems should be
        # using archives in the first place.
        if not self.problem_data.archive:
            raise InvalidInitException('can only use test case format specifiers if `archive` is set')
        return self.problem_data.archive.namelist()

    def _resolve_test_cases(self) -> List[dict]:
        test_cases = self.config.test_cases

        # We support several ways for specifying cases. The first is a list of cases, and requires no extra work.
        if test_cases is not None and isinstance(test_cases.unwrap(), list):
            return test_cases

        def get_with_default(name, default):
            if not test_cases:
                return default
            return test_cases[name] or default

        # If the `test_cases` node is None, we try to guess the testcase name format.
        self.config['test_cases'] = self._match_test_cases(
            self._problem_file_list(),
            re.compile(get_with_default('input_format', DEFAULT_TEST_CASE_INPUT_PATTERN), re.IGNORECASE),
            re.compile(get_with_default('output_format', DEFAULT_TEST_CASE_OUTPUT_PATTERN), re.IGNORECASE),
            iter(get_with_default('case_points', itertools.repeat(self.config.points))),
        )

        return self.config['test_cases']

    def load_checker(self, name: str) -> Checker:
        if name in self._checkers:
            return self._checkers[name]
        self._checkers[name] = checker = load_module_from_file(os.path.join(self.root_dir, name))
        return checker

    @property
    def grader_class(self) -> Type['BaseGrader']:
        from dmoj import graders

        if 'custom_judge' in self.config:
            return cast(Type['BaseGrader'], graders.CustomGrader)
        elif 'signature_grader' in self.config:
            return graders.SignatureGrader
        elif 'interactive' in self.config:
            return graders.BridgedInteractiveGrader
        else:
            return graders.StandardGrader

    def _resolve_archive_files(self) -> Optional[zipfile.ZipFile]:
        if self.config.archive:
            archive_path = os.path.join(self.root_dir, self.config.archive)
            if not os.path.exists(archive_path):
                raise InvalidInitException('archive file "%s" does not exist' % archive_path)
            try:
                archive = zipfile.ZipFile(archive_path, 'r')
            except zipfile.BadZipfile:
                raise InvalidInitException('bad archive: "%s"' % archive_path)
            return archive
        return None

    def _resolve_testcases(self, cfg, batch_no=0) -> List[BaseTestCase]:
        cases: List[BaseTestCase] = []
        for case_config in cfg:
            if 'batched' in case_config.raw_config:
                self._batch_counter += 1
                cases.append(
                    BatchedTestCase(
                        self._batch_counter,
                        case_config,
                        self,
                        self._resolve_testcases(case_config['batched'], self._batch_counter),
                    )
                )
            else:
                cases.append(TestCase(self._testcase_counter, batch_no, case_config, self))
                self._testcase_counter += 1
        return cases

    def cases(self) -> List[BaseTestCase]:
        pretest_test_cases = self.config.pretest_test_cases
        if self.run_pretests_only and pretest_test_cases:
            return self._resolve_testcases(pretest_test_cases)

        test_cases = self._resolve_testcases(self.config.test_cases)
        if pretest_test_cases:
            pretest_test_cases = self._resolve_testcases(pretest_test_cases)

            # Hack: force short-circuiting behavior
            for case in pretest_test_cases:
                case.points = 0

            test_cases = pretest_test_cases + test_cases

        return test_cases


class ProblemDataManager(dict):
    problem_root_dir: str
    archive: Optional[zipfile.ZipFile]

    def __init__(self, problem_root_dir: str, **kwargs):
        super().__init__(**kwargs)
        self.problem_root_dir = problem_root_dir
        self.archive = None

    def open(self, key: str):
        try:
            return open(os.path.join(self.problem_root_dir, key), 'rb')
        except IOError:
            if self.archive:
                zipinfo = self.archive.getinfo(key)
                return self.archive.open(zipinfo)
            raise KeyError('file "%s" could not be found in "%s"' % (key, self.problem_root_dir))

    def as_fd(self, key: str, normalize: bool = False) -> MmapableIO:
        memory = MemoryIO()
        with self.open(key) as f:
            if normalize:
                normalized_file_copy(f, memory)
            else:
                shutil.copyfileobj(f, memory)
        memory.seal()
        return memory

    def __missing__(self, key: str) -> bytes:
        with self.open(key) as f:
            return f.read()

    def __del__(self):
        if self.archive:
            self.archive.close()


class ProblemConfig(ConfigNode):
    def __init__(self, problem_data: ProblemDataManager, meta: dict = {}) -> None:
        try:
            doc = yaml.safe_load(problem_data['init.yml'])
        except (IOError, KeyError, ParserError, ScannerError) as e:
            raise InvalidInitException(str(e))
        else:
            if not doc:
                raise InvalidInitException('I find your lack of content disturbing.')
            super().__init__(
                doc,
                defaults={
                    'wall_time_factor': 3,
                    'output_prefix_length': 0 if 'signature_grader' in doc else 64,
                    'output_limit_length': 25165824,
                    'binary_data': False,
                    'short_circuit': True,
                    'dependencies': [],
                    'points': 1,
                    'symlinks': {},
                    'meta': meta,
                },
            )


class BatchedTestCase(BaseTestCase):
    batch_no: int

    def __init__(self, batch_no: int, config: ConfigNode, problem: Problem, cases: List[BaseTestCase]) -> None:
        self.config = config
        self.batch_no = batch_no
        self.points = config.points
        self.dependencies = config.dependencies
        self.batched_cases = cases
        if any(isinstance(case, BatchedTestCase) for case in self.batched_cases):
            raise InvalidInitException('nested batches')
        self.problem = problem
        if any(dependency >= batch_no for dependency in self.dependencies):
            raise InvalidInitException('dependencies depends on non-earlier batch')
        if any(dependency < 1 for dependency in self.dependencies):
            raise InvalidInitException('dependencies must be positive integers')

    def __str__(self) -> str:
        return f'BatchedTestCase(cases={self.batched_cases!s})'


class TestCase(BaseTestCase):
    batch: int
    output_prefix_length: int
    has_binary_data: bool
    _input_data_io: Optional[MmapableIO]
    _generated: Optional[Tuple[MmapableIO, bytes]]

    def __init__(self, count: int, batch_no: int, config: ConfigNode, problem: Problem):
        self.position = count
        self.batch = batch_no
        self.config = config
        self.problem = problem
        self.points = config.points
        self.output_prefix_length = config.output_prefix_length
        self.has_binary_data = config.binary_data
        self._generated = None
        self._input_data_io = None

    def _normalize(self, data: bytes) -> bytes:
        # Perhaps the correct answer may be 'no output', in which case it'll be
        # None here if sourced from a generator.
        data = data or b''

        # Leave binary and empty data alone, don't want to muck up newlines
        # there.
        if self.has_binary_data or not data:
            return data

        # Normalize all newline formats (\r\n, \r, \n) to \n, otherwise we have
        # problems with people creating data on Macs (\r newline) when judged
        # programs assume \n.
        data = data.replace(b'\r\n', b'\r').replace(b'\r', b'\n')

        # Some data might be missing a trailing newline, which makes the last
        # line in the file not-a-line.
        if not data.endswith(b'\n'):
            data += b'\n'

        return data

    def _run_generator(self, gen: Union[str, ConfigNode], args: Optional[Iterable[str]] = None) -> None:
        flags = []
        args = args or []

        # resource limits on how to run the generator
        time_limit = env.generator_time_limit
        memory_limit = env.generator_memory_limit
        compiler_time_limit = env.generator_compiler_time_limit
        lang = None  # Default to C/C++

        base = get_problem_root(self.problem.id)
        assert base is not None
        filenames: Union[str, list]
        if isinstance(gen, str):
            filenames = gen
        elif isinstance(gen.unwrap(), list):
            filenames = list(gen.unwrap())
        else:
            if isinstance(gen.source, str):
                filenames = gen.source
            elif isinstance(gen.source.unwrap(), list):
                filenames = list(gen.source.unwrap())
            else:
                raise InvalidInitException('invalid generator declaration')

            if gen.flags:
                flags += gen.flags
            if not args and gen.args:
                args += gen.args

            time_limit = gen.time_limit or time_limit
            memory_limit = gen.memory_limit or memory_limit
            compiler_time_limit = gen.compiler_time_limit or compiler_time_limit
            lang = gen.language

        if not isinstance(filenames, list):
            filenames = [filenames]

        filenames = [os.path.abspath(os.path.join(base, name)) for name in filenames]
        executor = compile_with_auxiliary_files(filenames, flags, lang, compiler_time_limit)

        # convert all args to str before launching; allows for smoother int passing
        assert args is not None
        args = map(str, args)

        input_io = MemoryIO()
        # Enable generators to write any size files.
        executor.fsize = -1

        # setting large buffers is really important, because otherwise stderr is unbuffered
        # and the generator begins calling into cptbox Python code really frequently
        proc = executor.launch(
            *args,
            time=time_limit,
            memory=memory_limit,
            stdin=subprocess.PIPE,
            stdout=input_io,
            stderr=subprocess.PIPE,
            stderr_buffer_size=65536,
            stdout_buffer_size=65536,
        )

        try:
            input = self.problem.problem_data[self.config['in']] if self.config['in'] else None
        except KeyError:
            input = None

        _, stderr = proc.unsafe_communicate(input)
        input_io.seal()
        self._generated = input_io, self._normalize(stderr)

        parse_helper_file_error(proc, executor, 'generator', stderr, time_limit, memory_limit)

    def input_data(self) -> bytes:
        return self.input_data_io().to_bytes()

    def input_data_io(self) -> MmapableIO:
        if self._input_data_io:
            return self._input_data_io

        result = self._input_data_io = self._make_input_data_io()
        return result

    def _make_input_data_io(self) -> MmapableIO:
        gen = self.config.generator

        # don't try running the generator if we specify an output file explicitly,
        # otherwise generator may segfault and we end up returning the output file anyway
        if gen and (not self.config['out'] or not self.config['in']):
            if self._generated is None:
                self._run_generator(gen, args=self.config.generator_args)
            assert self._generated is not None
            if self._generated[0]:
                return self._generated[0]

        # in file is optional
        if self.config['in']:
            return self.problem.problem_data.as_fd(self.config['in'], normalize=not self.has_binary_data)
        else:
            return MemoryIO(seal=True)

    def output_data(self) -> bytes:
        if self.config.out:
            return self._normalize(self.problem.problem_data[self.config.out])
        gen = self.config.generator
        if gen:
            if self._generated is None:
                self._run_generator(gen, args=self.config.generator_args)
            assert self._generated is not None
            return self._generated[1]
        return b''

    def checker(self) -> partial:
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

    def free_data(self) -> None:
        self._generated = None
        if self._input_data_io:
            self._input_data_io.close()

    def __str__(self) -> str:
        return f'TestCase(in={self.config["in"]},out={self.config["out"]},points={self.config["points"]})'

    # FIXME(tbrindus): this is a hack working around the fact we can't pickle these fields, but we do need parts of
    # TestCase itself on the other end of the IPC.
    _pickle_blacklist = ('_generated', 'config', 'problem', '_input_data_io')

    def __getstate__(self) -> dict:
        k = {k: v for k, v in self.__dict__.items() if k not in self._pickle_blacklist}
        return k

    def __setstate__(self, state) -> None:
        self.__dict__.update(state)
