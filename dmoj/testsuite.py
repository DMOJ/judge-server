import logging
import os
import platform
import sys
import traceback
from typing import cast

import yaml

from dmoj import contrib, executors, judgeenv
from dmoj.judge import Judge, Submission
from dmoj.judgeenv import get_problem_root, get_supported_problems
from dmoj.packet import PacketManager
from dmoj.utils.ansi import ansi_style, print_ansi

machine = platform.machine()
arch = {
    'i386': 'x86',
    'i486': 'x86',
    'i586': 'x86',
    'i686': 'x86',
    'x86_64': 'amd64',
    'aarch64': 'arm64',
    'armv6l': 'arm',
    'armv7l': 'arm',
    'armv8l': 'arm64',
}.get(machine, machine)
all_executors = executors.executors


class TestManager:
    def output(self, message):
        print(message)

    def fail(self, message):
        self.output('\t\t' + message.replace('\r\n', '\n').replace('\n', '\r\n\t\t'))
        self.failed = True

    def set_expected(
        self,
        codes_all,
        codes_cases,
        score_all,
        score_cases,
        feedback_all,
        feedback_cases,
        extended_feedback_all,
        extended_feedback_cases,
    ):
        self.failed = False
        self.codes_all = codes_all
        self.codes_cases = codes_cases
        self.score_all = score_all
        self.score_cases = score_cases
        self.feedback_all = feedback_all
        self.feedback_cases = feedback_cases
        self.extended_feedback_all = extended_feedback_all
        self.extended_feedback_cases = extended_feedback_cases

    def _receive_packet(self, packet):
        pass

    def supported_problems_packet(self, problems):
        pass

    def test_case_status_packet(self, position, result):
        code = result.readable_codes()[0]
        if position in self.codes_cases:
            if code not in self.codes_cases[position]:
                self.fail(
                    'Unexpected code for case %d: %s, expecting %s'
                    % (position, code, ', '.join(self.codes_cases[position]))
                )
        elif code not in self.codes_all:
            self.fail('Unexpected global code: %s, expecting %s' % (code, ', '.join(self.codes_all)))

        if position in self.score_cases:
            if result.points not in self.score_cases[position]:
                self.fail(
                    'Unexpected score for case %d: %s, expecting %s'
                    % (position, result.points, ', '.join(self.score_cases[position]))
                )
        elif self.score_all is not None and result.points not in self.score_all:
            self.fail(
                'Unexpected global score: %s, expecting %s' % (result.points, ', '.join(map(str, self.score_all)))
            )

        feedback = self.feedback_all
        if position in self.feedback_cases:
            feedback = self.feedback_cases[position]
        if feedback is not None and result.feedback not in feedback:
            self.fail('Unexpected feedback: "%s", expected: "%s"' % (result.feedback, '", "'.join(feedback)))

        extended_feedback = self.extended_feedback_all
        if position in self.extended_feedback_cases:
            extended_feedback = self.extended_feedback_cases[position]
        if extended_feedback is not None and result.extended_feedback not in extended_feedback:
            self.fail(
                'Unexpected extended feedback: "%s", expected: "%s"'
                % (result.extended_feedback, '", "'.join(extended_feedback))
            )

    def compile_error_packet(self, log):
        if 'CE' not in self.codes_all:
            self.fail('Unexpected compile error')

    def compile_message_packet(self, log):
        pass

    def internal_error_packet(self, message):
        allow_IE = 'IE' in self.codes_all
        allow_feedback = not self.feedback_all or any(map(lambda feedback: feedback in message, self.feedback_all))
        if not allow_IE or not allow_feedback:
            self.fail('Unexpected internal error:\n' + message)

    def begin_grading_packet(self, is_pretested):
        pass

    def grading_end_packet(self):
        pass

    def batch_begin_packet(self):
        pass

    def batch_end_packet(self):
        pass

    def current_submission_packet(self):
        pass

    def submission_aborted_packet(self):
        pass

    def submission_acknowledged_packet(self, sub_id):
        pass


class Tester:
    all_codes = {'AC', 'IE', 'TLE', 'MLE', 'OLE', 'RTE', 'IR', 'WA', 'CE', 'SC'}

    def __init__(self, problem_regex=None, case_regex=None):
        self.manager = TestManager()
        self.manager.output = self.error_output
        self.judge = Judge(cast(PacketManager, self.manager))
        self.sub_id = 0
        self.problem_regex = problem_regex
        self.case_regex = case_regex

        self.case_files = ['test.yml']

        self.case_files += ['test.posix.yml']
        if 'freebsd' in sys.platform:
            self.case_files += ['test.freebsd.yml']
            if not sys.platform.startswith('freebsd'):
                self.case_files += ['test.kfreebsd.yml']
        elif sys.platform.startswith('linux'):
            self.case_files += ['test.linux.yml']

    def output(self, message=''):
        print(message)

    def error_output(self, message):
        print_ansi('#ansi[%s](red)' % message)

    def test_all(self):
        total_fails = 0

        for problem in get_supported_problems():
            if self.problem_regex is not None and not self.problem_regex.match(problem):
                continue
            root = get_problem_root(problem)
            test_dir = os.path.join(root, 'tests')
            if os.path.isdir(test_dir):
                fails = self.test_problem(problem, test_dir)
                if fails:
                    self.output(
                        ansi_style('Problem #ansi[%s](cyan|bold) #ansi[failed %d case(s)](red|bold).')
                        % (problem, fails)
                    )
                else:
                    self.output(ansi_style('Problem #ansi[%s](cyan|bold) passed with flying colours.') % problem)
                self.output()
                total_fails += fails

        return total_fails

    def test_problem(self, problem, test_dir):
        self.output(ansi_style('Testing problem #ansi[%s](cyan|bold)...') % problem)
        fails = 0

        dirs = [case for case in os.listdir(test_dir) if self.case_regex is None or self.case_regex.match(case)]
        for i in range(len(dirs)):
            case = dirs[i]
            case_dir = os.path.join(test_dir, case)
            if os.path.isdir(case_dir):
                self.output(
                    ansi_style('\tRunning test case #ansi[%s](yellow|bold) for #ansi[%s](cyan|bold)...')
                    % (case, problem)
                )
                try:
                    case_fails = self.run_test_case(problem, case, case_dir)
                except Exception:
                    fails += 1
                    self.output(ansi_style('\t#ansi[Test case failed with exception:](red|bold)'))
                    self.output(traceback.format_exc())
                else:
                    self.output(
                        ansi_style('\tResult of case #ansi[%s](yellow|bold) for #ansi[%s](cyan|bold): ')
                        % (case, problem)
                        + ansi_style(['#ansi[Failed](red|bold)', '#ansi[Success](green|bold)'][not case_fails])
                    )
                    fails += case_fails

                if i != len(dirs) - 1:
                    self.output()

        return fails

    def run_test_case(self, problem, case, case_dir):
        config = {}
        for file in self.case_files:
            try:
                with open(os.path.join(case_dir, file)) as f:
                    config.update(yaml.safe_load(f.read()))
            except IOError:
                pass

        if not config:
            self.output(ansi_style('\t\t#ansi[Skipped](magenta|bold) - No usable test config'))
            return 0

        if 'arch' in config and arch not in config['arch']:
            self.output(ansi_style('\t\t#ansi[Skipped](magenta|bold) - No usable test config'))
            return 0

        return self._run_test_case(problem, case_dir, config)

    def _run_test_case(self, problem, case_dir, config):
        if 'skip' in config and config['skip']:
            self.output(ansi_style('\t\t#ansi[Skipped](magenta|bold) - Unsupported on current platform'))
            return 0

        language = config['language']
        if language not in all_executors:
            self.output(ansi_style('\t\t#ansi[Skipped](magenta|bold) - Language not supported'))
            return 0
        time = config['time']
        memory = config['memory']
        if isinstance(config['source'], str):
            with open(os.path.join(case_dir, config['source'])) as f:
                sources = [f.read()]
        else:
            sources = []
            for file in config['source']:
                with open(os.path.join(case_dir, file)) as f:
                    sources += [f.read()]
        codes_all, codes_cases = self.parse_expect(
            config.get('expect', 'AC'), config.get('cases', {}), self.parse_expected_codes
        )
        score_all, score_cases = self.parse_expect(config.get('score'), config.get('score_cases', {}), self.parse_score)
        feedback_all, feedback_cases = self.parse_expect(
            config.get('feedback'), config.get('feedback_cases', {}), self.parse_feedback
        )
        extended_feedback_all, extended_feedback_cases = self.parse_expect(
            config.get('extended_feedback'), config.get('extended_feedback_cases', {}), self.parse_feedback
        )

        def output_case(data):
            self.output('\t\t' + data)

        fails = 0
        for source in sources:
            self.sub_id += 1
            self.manager.set_expected(
                codes_all,
                codes_cases,
                score_all,
                score_cases,
                feedback_all,
                feedback_cases,
                extended_feedback_all,
                extended_feedback_cases,
            )
            self.judge.begin_grading(
                Submission(self.sub_id, problem, language, source, time, memory, False, {}),
                blocking=True,
                report=output_case,
            )
            fails += self.manager.failed
        return fails

    def parse_expect(self, all, cases, func):
        expect = func(all)
        if isinstance(cases, list):
            cases = enumerate(cases, 1)
        else:
            cases = cases.items()
        case_expect = {id: func(codes) for id, codes in cases}
        return expect, case_expect

    def parse_expected_codes(self, codes):
        if codes == '*':
            return self.all_codes
        elif isinstance(codes, str):
            assert codes in self.all_codes
            return {codes}
        else:
            result = set(codes)
            assert not (result - self.all_codes)
            return result

    def parse_score(self, score):
        if score is None or score == '*':
            return None
        elif isinstance(score, (str, int)):
            return {int(score)}
        else:
            return set(map(int, score))

    def parse_feedback(self, feedback):
        if feedback is None or feedback == '*':
            return None
        elif isinstance(feedback, str):
            return {feedback}
        else:
            return set(feedback)


def main():
    judgeenv.load_env(cli=True, testsuite=True)

    logging.basicConfig(
        filename=judgeenv.log_file, level=judgeenv.log_level, format='%(levelname)s %(asctime)s %(module)s %(message)s'
    )

    executors.load_executors()
    contrib.load_contrib_modules()

    tester = Tester(judgeenv.problem_regex, judgeenv.case_regex)
    fails = tester.test_all()
    print()
    print('Test complete.')
    if fails:
        print_ansi('#ansi[A total of %d case(s) failed](red|bold).' % fails)
    else:
        print_ansi('#ansi[All cases passed.](green|bold)')
    raise SystemExit(int(fails != 0))


if __name__ == '__main__':
    main()
