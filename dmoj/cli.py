from __future__ import print_function

import os
import sys
from collections import OrderedDict

from six.moves import input

from dmoj.judge import Judge
from dmoj.utils.ansi import ansi_style


class LocalPacketManager(object):
    def __init__(self, judge):
        self.judge = judge

    def _receive_packet(self, packet):
        pass

    def supported_problems_packet(self, problems):
        pass

    def test_case_status_packet(self, position, result):
        pass

    def compile_error_packet(self, log):
        pass

    def compile_message_packet(self, log):
        pass

    def internal_error_packet(self, message):
        pass

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

    def run(self):
        pass


class LocalJudge(Judge):
    def __init__(self):
        self.packet_manager = LocalPacketManager(self)
        self.submission_id_counter = 0
        self.graded_submissions = []
        super(LocalJudge, self).__init__()


class InvalidCommandException(Exception):
    def __init__(self, message=None):
        self.message = message


commands = OrderedDict()


def register(command):
    commands[command.name] = command


def main():
    global commands
    import logging
    from dmoj import judgeenv, executors

    judgeenv.load_env(cli=True)

    # Emulate ANSI colors with colorama
    if os.name == 'nt' and not judgeenv.no_ansi_emu:
        try:
            from colorama import init
            init()
        except ImportError:
            pass

    executors.load_executors()

    print('Running local judge...')

    logging.basicConfig(filename=judgeenv.log_file, level=logging.INFO,
                        format='%(levelname)s %(asctime)s %(module)s %(message)s')

    judge = LocalJudge()

    for warning in judgeenv.startup_warnings:
        print(ansi_style('#ansi[Warning: %s](yellow)' % warning))
    del judgeenv.startup_warnings
    print()

    from dmoj.commands import all_commands
    for command in all_commands:
        register(command(judge))

    with judge:
        try:
            judge.listen()

            while True:
                command = input(ansi_style("#ansi[dmoj](magenta)#ansi[>](green) ")).strip()

                line = command.split(' ')
                if line[0] in commands:
                    cmd = commands[line[0]]
                    try:
                        cmd.execute(line[1:])
                    except InvalidCommandException as e:
                        if e.message:
                            print(ansi_style("#ansi[%s](red|bold)\n" % e.message))
                        print()
                else:
                    print(ansi_style('#ansi[Unrecognized command %s](red|bold)' % line[0]))
                    print()
        except (EOFError, KeyboardInterrupt):
            print()
        finally:
            judge.murder()


if __name__ == '__main__':
    sys.exit(main())
