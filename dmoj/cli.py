import atexit
import readline
import shlex
import sys
from typing import List, cast

from dmoj.commands.base_command import GradedSubmission
from dmoj.error import InvalidCommandException
from dmoj.judge import Judge
from dmoj.packet import PacketManager
from dmoj.utils.ansi import ansi_style, print_ansi


class LocalPacketManager:
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

    def submission_aborted_packet(self):
        pass

    def submission_acknowledged_packet(self, sub_id):
        pass

    def run(self):
        pass

    def close(self):
        pass


class LocalJudge(Judge):
    graded_submissions: List[GradedSubmission]

    def __init__(self):
        super().__init__(cast(PacketManager, LocalPacketManager(self)))
        self.submission_id_counter = 0
        self.graded_submissions = []


def main():
    sys.exit(cli_main())


def cli_main():
    import logging
    from dmoj import judgeenv, contrib, executors

    judgeenv.load_env(cli=True)

    logging.basicConfig(
        filename=judgeenv.log_file, level=judgeenv.log_level, format='%(levelname)s %(asctime)s %(module)s %(message)s'
    )

    executors.load_executors()
    contrib.load_contrib_modules()

    try:
        readline.read_history_file(judgeenv.cli_history_file)
    except FileNotFoundError:
        pass
    atexit.register(readline.write_history_file, judgeenv.cli_history_file)

    print('Running local judge...')

    judge = LocalJudge()

    for warning in judgeenv.startup_warnings:
        print_ansi('#ansi[Warning: %s](yellow)' % warning)
    del judgeenv.startup_warnings
    print()

    from dmoj.commands import all_commands, commands, register_command

    for command in all_commands:
        register_command(command(judge))

    def run_command(line):
        if not line:
            return 127

        if line[0] in commands:
            cmd = commands[line[0]]
            try:
                return cmd.execute(line[1:])
            except InvalidCommandException as e:
                if e.message:
                    print_ansi('#ansi[%s](red|bold)\n' % e.message)
                print()
                return 1
        else:
            print_ansi('#ansi[Unrecognized command %s](red|bold)' % line[0])
            print()
            return 127

    try:
        judge.listen()

        if judgeenv.cli_command:
            return run_command(judgeenv.cli_command)
        else:
            while True:
                command = input(ansi_style('#ansi[dmoj](magenta)#ansi[>](green) ')).strip()
                run_command(shlex.split(command))
    except (EOFError, KeyboardInterrupt):
        print()
    finally:
        judge.murder()


if __name__ == '__main__':
    main()
