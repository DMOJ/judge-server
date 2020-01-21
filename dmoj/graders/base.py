import itertools
import re

from dmoj.config import ConfigNode
from dmoj.problem import BatchedTestCase, DEFAULT_TEST_CASE_INPUT_PATTERN, DEFAULT_TEST_CASE_OUTPUT_PATTERN, TestCase
from dmoj.utils.unicode import utf8bytes


class BaseGrader:
    def __init__(self, judge, problem, language, source, meta):
        self.source = utf8bytes(source)
        self.language = language
        self.problem = problem
        self.judge = judge
        self.meta = ConfigNode(meta)
        self.binary = self._generate_binary()
        self.is_pretested = self.meta.pretests_only and 'pretest_test_cases' in self.problem.config
        self._terminate_grading = False
        self._current_proc = None
        self._batch_counter = 0
        self._testcase_counter = 0

    def grade(self, case):
        raise NotImplementedError

    def _generate_binary(self):
        raise NotImplementedError

    def terminate_grading(self):
        self._terminate_grading = True
        if self._current_proc:
            try:
                self._current_proc.kill()
            except OSError:
                pass

    def _match_test_cases(self, filenames, input_case_pattern, output_case_pattern, case_points):
        def try_match_int(match, group):
            try:
                val = match.group(group)
            except IndexError:
                return None

            try:
                return int(val)
            except (ValueError, TypeError):
                return val

        def parse_position(pattern, filename):
            match = pattern.match(filename)
            if not match:
                return None

            # Allow batches and case numbers to be alphanumeric, in which case we will sort them lexicographically.
            # Still attempt to process them as integers first, though, since most problems will use this format.
            return try_match_int(match, 'batch'), try_match_int(match, 'case')

        class _TestCase:
            input_file = None
            output_file = None

        # Match all cases with the same (batch, position) mapping.
        groups = defaultdict(lambda: defaultdict(_TestCase))
        batch_ids = set()

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

                setattr(groups[batch or case][case], filetype, testcase_file)

        test_cases = []
        for batch_or_case_id in sorted(groups.keys()):
            group_cases = groups[batch_or_case_id]
            if batch_or_case_id in batch_ids:
                test_cases.append({
                    'batched': [{
                        'in': testcase.input_file,
                        'out': testcase.output_file,
                    } for _, testcase in sorted(group_cases.items())],
                    'points': next(case_points),
                })
            else:
                if len(group_cases) > 1:
                    raise InvalidInitException('problem has conflicting test cases: %s' % group_cases)
                test_case = next(iter(group_cases.values()))
                test_cases.append({
                    'in': test_case.input_file,
                    'out': test_case.output_file,
                    'points': next(case_points),
                })

        return test_cases

    def _resolve_testcases(self, cfg, batch_no=0):
        def get_with_default(name, default):
            if not cfg:
                return default
            return cfg[name] or default

        # We support several ways for specifying cases. The first is a list of cases, and requires no extra work.
        if cfg is None or not isinstance(cfg.unwrap(), list):
            # If the `test_cases` node is None, we try to guess the testcase name format.
            cfg = self._match_test_cases(
                self.problem.problem_file_list(),
                re.compile(get_with_default('input_format', DEFAULT_TEST_CASE_INPUT_PATTERN), re.IGNORECASE),
                re.compile(get_with_default('output_format', DEFAULT_TEST_CASE_OUTPUT_PATTERN), re.IGNORECASE),
                iter(get_with_default('case_points', itertools.repeat(1))),
            )

        cases = []
        for case_config in cfg:
            if 'batched' in case_config.raw_config:
                self._batch_counter += 1
                cases.append(BatchedTestCase(self._batch_counter, case_config, self.problem,
                                             self._resolve_testcases(case_config['batched'], self._batch_counter)))
            else:
                cases.append(TestCase(self._testcase_counter, batch_no, case_config, self.problem))
                self._testcase_counter += 1
        return cases

    def cases(self):
        key = 'pretest_test_cases' if self.is_pretested else 'test_cases'
        return self._resolve_testcases(self.problem.config[key])
