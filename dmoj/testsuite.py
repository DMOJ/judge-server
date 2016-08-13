import os
import traceback

import yaml

from dmoj import judgeenv, executors
from dmoj.judge import Judge
from dmoj.judgeenv import get_supported_problems, get_problem_root
from dmoj.utils.ansi import ansi_style

all_executors = executors.executors


class TestManager(object):
    def output(self, message):
        print message

    def fail(self, message):
        self.output(message)
        self.failed = True

    def set_expected(self, all, cases):
        self.failed = False
        self.codes_all = all
        self.codes_cases = cases

    def _receive_packet(self, packet):
        pass

    def supported_problems_packet(self, problems):
        pass

    def test_case_status_packet(self, position, result):
        code = result.readable_codes()[0]
        if position in self.codes_cases:
            if code not in self.codes_cases[position]:
                self.fail('Unexpected code for case %d: %s' % (position, code))
        elif code not in self.codes_all:
            self.fail('Unexpected global code: %s' % code)

    def compile_error_packet(self, log):
        if 'CE' not in self.codes_all:
            self.fail('Unexpected compile error')

    def compile_message_packet(self, log):
        pass

    def internal_error_packet(self, message):
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

    def submission_terminated_packet(self):
        pass

    def submission_acknowledged_packet(self, sub_id):
        pass


class TestJudge(Judge):
    def __init__(self, manager):
        self.packet_manager = manager
        super(TestJudge, self).__init__()


class Tester(object):
    all_codes = {'AC', 'IE', 'TLE', 'MLE', 'OLE', 'RTE', 'IR', 'WA', 'SC'}

    def __init__(self):
        self.manager = TestManager()
        self.manager.output = self.error_output
        self.judge = TestJudge(self.manager)
        self.sub_id = 0

    def output(self, message=''):
        print message

    def error_output(self, message):
        print ansi_style('#ansi[%s](red)') % message

    def test_all(self):
        total_fails = 0

        for problem, _ in get_supported_problems():
            root = get_problem_root(problem)
            test_dir = os.path.join(root, 'tests')
            if os.path.isdir(test_dir):
                fails = self.test_problem(problem, test_dir)
                if fails:
                    self.output(ansi_style('Problem #ansi[%s](cyan|bold) #ansi[failed %d case(s)](red|bold).')
                                % (problem, fails))
                else:
                    print ansi_style('Problem #ansi[%s](cyan|bold) passed with flying colours.') % problem
                total_fails += fails

        return total_fails

    def test_problem(self, problem, test_dir):
        self.output(ansi_style('Testing problem #ansi[%s](cyan|bold)...') % problem)
        self.output()
        fails = 0

        for case in os.listdir(test_dir):
            case_dir = os.path.join(test_dir, case)
            if os.path.isdir(case_dir):
                self.output(ansi_style('Running test case #ansi[%s](yellow|bold) for #ansi[%s](cyan|bold)...')
                            % (case, problem))
                try:
                    case_fails = self.run_test_case(problem, case, case_dir)
                except Exception:
                    fails += 1
                    self.output(ansi_style('#ansi[Test case failed with exception:](red|bold)'))
                    self.output(traceback.format_exc())
                else:
                    self.output(ansi_style('Result of case #ansi[%s](yellow|bold) for #ansi[%s](cyan|bold): ')
                                % (case, problem) +
                                ansi_style(['#ansi[Failed](red|bold)', '#ansi[Success](green|bold)'][not case_fails]))
                    fails += case_fails
                self.output()
        return fails

    def run_test_case(self, problem, case, case_dir):
        with open(os.path.join(case_dir, 'test.yml')) as f:
            config = yaml.safe_load(f.read())

        language = config['language']
        if language not in all_executors:
            self.output(ansi_style('    #ansi[Skipped](magenta|bold) - Language not supported'))
            return 0
        time = config['time']
        memory = config['memory']
        if isinstance(config['source'], (str, unicode)):
            with open(os.path.join(case_dir, config['source'])) as f:
                sources = [f.read()]
        else:
            sources = []
            for file in config['source']:
                with open(os.path.join(case_dir, file)) as f:
                    sources += [f.read()]
        expect = self.parse_expected_codes(config['expect'])
        cases = config.get('cases', {})
        if isinstance(cases, list):
            cases = enumerate(cases, 1)
        else:
            cases = cases.iteritems()
        case_expect = {id: self.parse_expected_codes(codes) for id, codes in cases}

        fails = 0
        for source in sources:
            self.sub_id += 1
            self.manager.set_expected(expect, case_expect)
            self.judge.begin_grading(self.sub_id, problem, language, source, time, memory,
                                     short_circuit=False, pretests_only=False, blocking=True)
            fails += self.manager.failed
        return fails

    def parse_expected_codes(self, codes):
        if codes == '*':
            return self.all_codes
        elif isinstance(codes, (str, unicode)):
            assert codes in self.all_codes
            return {codes}
        else:
            result = set(codes)
            assert not (result - self.all_codes)


def main():
    judgeenv.load_env(cli=True, testsuite=True)

    # Emulate ANSI colors with colorama
    if os.name == 'nt' and not judgeenv.no_ansi_emu:
        try:
            from colorama import init
            init()
        except ImportError:
            pass

    executors.load_executors()

    tester = Tester()
    fails = tester.test_all()
    print
    print 'Test complete'
    if fails:
        print ansi_style('#ansi[A total of %d case(s) failed](red|bold).') % fails
    else:
        print ansi_style('#ansi[All cases passed.](green|bold)')
    raise SystemExit(int(fails != 0))

if __name__ == '__main__':
    main()
