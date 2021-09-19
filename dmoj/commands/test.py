import sys
import traceback
from typing import Any, Dict, Iterable

from dmoj.commands.base_command import Command
from dmoj.error import InvalidCommandException
from dmoj.judgeenv import get_problem_root, get_supported_problems
from dmoj.problem import ProblemConfig, ProblemDataManager
from dmoj.testsuite import Tester
from dmoj.utils.ansi import ansi_style, print_ansi


class ProblemTester(Tester):
    def run_problem_tests(self, problem_id: str) -> int:
        self.output(ansi_style(f'Testing problem #ansi[{problem_id}](cyan|bold)...'))

        config = ProblemConfig(ProblemDataManager(get_problem_root(problem_id)))

        if not config or 'tests' not in config or not config['tests']:
            self.output(ansi_style('\t#ansi[Skipped](magenta|bold) - No tests found'))
            return 0

        fails = 0
        for test in config['tests']:
            # Do this check here as we need some way to identify the test
            if 'source' not in test:
                self.output(ansi_style('\t[Skipped](magenta|bold) - No source found for test'))
                continue

            test_name = test.get('label', test['source'])
            self.output(ansi_style(f'\tRunning test #ansi[{test_name}](yellow|bold)'))
            try:
                test_fails = self.run_test(problem_id, test)
            except Exception:
                fails += 1
                self.output(ansi_style('\t#ansi[Test failed with exception:](red|bold)'))
                self.output(traceback.format_exc())
            else:
                self.output(
                    ansi_style(f'\tResult of test #ansi[{test_name}](yellow|bold): ')
                    + ansi_style(['#ansi[Failed](red|bold)', '#ansi[Success](green|bold)'][not test_fails])
                )
                fails += test_fails

        return fails

    @staticmethod
    def _check_targets(targets: Iterable[str]) -> bool:
        if 'posix' in targets:
            return True
        if 'freebsd' in sys.platform:
            if 'freebsd' in targets:
                return True
            if not sys.platform.startswith('freebsd') and 'kfreebsd' in targets:
                return True
        elif sys.platform.startswith('linux') and 'linux' in targets:
            return True
        return False

    def run_test(self, problem_id: str, config: Dict[str, Any]) -> int:
        if 'targets' in config and not self._check_targets(config['targets']):
            return 0

        return self._run_test_case(problem_id, get_problem_root(problem_id), config)


class TestCommand(Command):
    name = 'test'
    help = 'Runs tests on problems.'

    def _populate_parser(self) -> None:
        self.arg_parser.add_argument('problem_ids', nargs='+', help='ids of problems to test')

    def execute(self, line: str) -> int:
        args = self.arg_parser.parse_args(line)

        problem_ids = args.problem_ids
        supported_problems = set(get_supported_problems())

        unknown_problems = ', '.join(f"'{i}'" for i in problem_ids if i not in supported_problems)
        if unknown_problems:
            raise InvalidCommandException(f'unknown problem(s) {unknown_problems}')

        tester = ProblemTester()
        total_fails = 0
        for problem_id in problem_ids:
            fails = tester.run_problem_tests(problem_id)
            if fails:
                print_ansi(f'Problem #ansi[{problem_id}](cyan|bold) #ansi[failed {fails} case(s)](red|bold).')
            else:
                print_ansi(f'Problem #ansi[{problem_id}](cyan|bold) passed with flying colours.')
            print()
            total_fails += fails

        print()
        print('Test complete.')
        if total_fails:
            print_ansi(f'#ansi[A total of {total_fails} test(s) failed](red|bold)')
        else:
            print_ansi('#ansi[All tests passed.](green|bold)')

        return total_fails
