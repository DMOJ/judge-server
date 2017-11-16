import argparse
import os
import re
import sys
from collections import OrderedDict
from itertools import izip_longest
from operator import itemgetter
import difflib
import tempfile
import subprocess

import pygments
from pygments import lexers
from pygments import formatters

from dmoj import judgeenv
from dmoj.executors import executors
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


commands = OrderedDict()


def register(command):
    commands[command.name] = command


class InvalidCommandException(Exception):
    def __init__(self, message=None):
        self.message = message


class CommandArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        raise InvalidCommandException

    def exit(self, status=0, message=None):
        if message:
            self._print_message(message, sys.stderr)
        raise InvalidCommandException


class Command(object):
    name = 'command'
    help = ''

    def __init__(self, judge):
        self.judge = judge
        self.arg_parser = CommandArgumentParser(prog=self.name, description=self.help)
        self._populate_parser()

    def get_source(self, source_file):
        try:
            with open(os.path.realpath(source_file)) as f:
                return f.read()
        except Exception as io:
            raise InvalidCommandException(str(io))

    def get_submission_data(self, submission_id):
        # don't wrap around
        if submission_id > 0:
            try:
                return self.judge.graded_submissions[submission_id - 1]
            except IndexError:
                pass

        raise InvalidCommandException("invalid submission '%d'" % submission_id)

    def open_editor(self, lang, src=''):
        file_suffix = executors[lang].Executor.ext
        editor = os.environ.get('EDITOR')
        if editor:
            with tempfile.NamedTemporaryFile(suffix=file_suffix) as temp:
                temp.write(src)
                temp.flush()
                subprocess.call([editor, temp.name])
                temp.seek(0)
                src = temp.read()
        else:
            print ansi_style('#ansi[$EDITOR not set, falling back to stdin](yellow)\n')
            src = []
            try:
                while True:
                    s = raw_input()
                    if s.strip() == ':q':
                        raise EOFError
                    src.append(s)
            except EOFError:  # Ctrl+D
                src = '\n'.join(src)
            except Exception as io:
                raise InvalidCommandException(str(io))
        return src

    def _populate_parser(self):
        pass

    def execute(self, line):
        raise NotImplementedError


class ListProblemsCommand(Command):
    name = 'problems'
    help = 'Lists the problems available to be graded on this judge.'

    def _populate_parser(self):
        self.arg_parser.add_argument('filter', nargs='?', help='regex filter for problem names (optional)')
        self.arg_parser.add_argument('-l', '--limit', type=int, help='limit number of results', metavar='<limit>')

    def execute(self, line):
        _args = self.arg_parser.parse_args(line)

        if _args.limit is not None and _args.limit <= 0:
            raise InvalidCommandException('--limit must be >= 0')

        all_problems = judgeenv.get_supported_problems()

        if _args.filter:
            r = re.compile(_args.filter)
            all_problems = filter(lambda x: r.match(x[0]) is not None, all_problems)

        if _args.limit:
            all_problems = all_problems[:_args.limit]

        if len(all_problems):
            problems = iter(map(itemgetter(0), all_problems))
            max_len = max(len(p[0]) for p in all_problems)
            for row in izip_longest(*[problems] * 4, fillvalue=''):
                print ' '.join(('%*s' % (-max_len, row[i])) for i in xrange(4))
            print
        else:
            raise InvalidCommandException('No problems matching filter found.')


class QuitCommand(Command):
    name = 'quit'
    help = 'Exits the DMOJ command-line interface.'

    def execute(self, line):
        sys.exit(0)


class HelpCommand(Command):
    name = 'help'
    help = 'Prints listing of commands.'

    def execute(self, line):
        print "Run `command -h/--help` for individual command usage."
        for name, command in commands.iteritems():
            if command == self:
                continue
            print '  %s: %s' % (name, command.help)
        print


class SubmitCommand(Command):
    name = 'submit'
    help = 'Grades a submission.'

    def _populate_parser(self):
        self.arg_parser.add_argument('problem_id', help='id of problem to grade')
        self.arg_parser.add_argument('language_id', nargs='?', default=None,
                                     help='id of the language to grade in (e.g., PY2)')
        self.arg_parser.add_argument('source_file', nargs='?', default=None,
                                     help='path to submission source (optional)')
        self.arg_parser.add_argument('-tl', '--time-limit', type=float, help='time limit for grading, in seconds',
                                     default=2.0, metavar='<time limit>')
        self.arg_parser.add_argument('-ml', '--memory-limit', type=int, help='memory limit for grading, in kilobytes',
                                     default=65536, metavar='<memory limit>')

    def execute(self, line):
        args = self.arg_parser.parse_args(line)

        problem_id = args.problem_id
        language_id = args.language_id
        time_limit = args.time_limit
        memory_limit = args.memory_limit
        source_file = args.source_file

        if language_id not in executors:
            source_file = language_id
            language_id = None  # source file / language id optional

        if problem_id not in map(itemgetter(0), judgeenv.get_supported_problems()):
            raise InvalidCommandException("unknown problem '%s'" % problem_id)
        elif not language_id:
            if source_file:
                filename, dot, ext = source_file.partition('.')
                if not ext:
                    raise InvalidCommandException('invalid file name')
                else:
                    # TODO: this should be a proper lookup elsewhere
                    ext = ext.upper()
                    language_id = {
                        'PY': 'PY2',
                        'CPP': 'CPP11',
                        'JAVA': 'JAVA8'
                    }.get(ext, ext)
            else:
                raise InvalidCommandException("no language is selected")
        elif language_id not in executors:
            raise InvalidCommandException("unknown language '%s'" % language_id)
        elif time_limit <= 0:
            raise InvalidCommandException('--time-limit must be >= 0')
        elif memory_limit <= 0:
            raise InvalidCommandException('--memory-limit must be >= 0')

        src = self.get_source(source_file) if source_file else self.open_editor(language_id)

        self.judge.submission_id_counter += 1
        self.judge.graded_submissions.append((problem_id, language_id, src, time_limit, memory_limit))
        self.judge.begin_grading(self.judge.submission_id_counter, problem_id, language_id, src, time_limit,
                                 memory_limit, False, False, blocking=True)


class ResubmitCommand(Command):
    name = 'resubmit'
    help = 'Resubmit a submission with different parameters.'

    def _populate_parser(self):
        self.arg_parser.add_argument('submission_id', type=int, help='id of submission to resubmit')
        self.arg_parser.add_argument('-p', '--problem', help='id of problem to grade', metavar='<problem id>')
        self.arg_parser.add_argument('-l', '--language', help='id of the language to grade in (e.g., PY2)',
                                     metavar='<language id>')
        self.arg_parser.add_argument('-tl', '--time-limit', type=float, help='time limit for grading, in seconds',
                                     metavar='<time limit>')
        self.arg_parser.add_argument('-ml', '--memory-limit', type=int, help='memory limit for grading, in kilobytes',
                                     metavar='<memory limit>')

    def execute(self, line):
        args = self.arg_parser.parse_args(line)

        id, lang, src, tl, ml = self.get_submission_data(args.submission_id)

        id = args.problem or id
        lang = args.language or lang
        tl = args.time_limit or tl
        ml = args.memory_limit or ml

        if id not in map(itemgetter(0), judgeenv.get_supported_problems()):
            raise InvalidCommandException("unknown problem '%s'" % id)
        elif lang not in executors:
            raise InvalidCommandException("unknown language '%s'" % lang)
        elif tl <= 0:
            raise InvalidCommandException('--time-limit must be >= 0')
        elif ml <= 0:
            raise InvalidCommandException('--memory-limit must be >= 0')

        src = self.open_editor(lang, src)

        self.judge.submission_id_counter += 1
        self.judge.graded_submissions.append((id, lang, src, tl, ml))
        self.judge.begin_grading(self.judge.submission_id_counter, id, lang, src, tl, ml, False, False, blocking=True)


class RejudgeCommand(Command):
    name = 'rejudge'
    help = 'Rejudge a submission.'

    def _populate_parser(self):
        self.arg_parser.add_argument('submission_id', type=int, help='id of submission to rejudge')

    def execute(self, line):
        args = self.arg_parser.parse_args(line)
        problem, lang, src, tl, ml = self.get_submission_data(args.submission_id)

        self.judge.begin_grading(self.judge.submission_id_counter, problem, lang, src, tl, ml, False, False,
                                 blocking=True)


class ListSubmissionsCommand(Command):
    name = 'submissions'
    help = 'List past submissions.'

    def _populate_parser(self):
        self.arg_parser.add_argument('-l', '--limit', type=int, help='limit number of results by most recent',
                                     metavar='<limit>')

    def execute(self, line):
        args = self.arg_parser.parse_args(line)

        if args.limit is not None and args.limit <= 0:
            raise InvalidCommandException("--limit must be >= 0")

        submissions = self.judge.graded_submissions if not args.limit else self.judge.graded_submissions[:args.limit]

        for i, (problem, lang, src, tl, ml) in enumerate(submissions):
            print ansi_style('#ansi[%s](yellow)/#ansi[%s](green) in %s' % (problem, i + 1, lang))
        print


class DifferenceCommand(Command):
    name = 'diff'
    help = 'Shows difference between two files.'

    def _populate_parser(self):
        self.arg_parser.add_argument('id_or_source_1', help='id or path of first source', metavar='<source 1>')
        self.arg_parser.add_argument('id_or_source_2', help='id or path of second source', metavar='<source 2>')

    def get_data(self, id_or_source):
        try:
            _, _, src, _, _ = self.get_submission_data(int(id_or_source))
        except ValueError:
            src = self.get_source(id_or_source)

        return src.splitlines()

    def execute(self, line):
        args = self.arg_parser.parse_args(line)

        file1 = args.id_or_source_1
        file2 = args.id_or_source_2

        data1 = self.get_data(file1)
        data2 = self.get_data(file2)

        difference = list(difflib.unified_diff(data1, data2, fromfile=file1, tofile=file2, lineterm=''))
        if not difference:
            print 'no difference\n'
        else:
            file_diff = '\n'.join(difference)
            print pygments.highlight(file_diff, pygments.lexers.DiffLexer(), pygments.formatters.Terminal256Formatter())


class ShowCommand(Command):
    name = 'show'
    help = 'Shows file based on submission ID or filename.'

    def _populate_parser(self):
        self.arg_parser.add_argument('id_or_source', help='id or path of submission to show', metavar='<source>')

    def get_data(self, id_or_source):
        try:
            id = int(id_or_source)
        except ValueError:
            src = self.get_source(id_or_source)
            lexer = pygments.lexers.get_lexer_for_filename(id_or_source)
        else:
            _, lang, src, _, _ = self.get_submission_data(id)

            # TODO: after executor->extension mapping is built-in to the judge, redo this
            if lang in ['PY2', 'PYPY2']:
                lexer = pygments.lexers.PythonLexer()
            elif lang in ['PY3', 'PYPY3']:
                lexer = pygments.lexers.Python3Lexer()
            else:
                lexer = pygments.lexers.guess_lexer(src)

        return src, lexer

    def execute(self, line):
        args = self.arg_parser.parse_args(line)
        data, lexer = self.get_data(args.id_or_source)

        print pygments.highlight(data, lexer, pygments.formatters.Terminal256Formatter())


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

    print 'Running local judge...'

    logging.basicConfig(filename=judgeenv.log_file, level=logging.INFO,
                        format='%(levelname)s %(asctime)s %(module)s %(message)s')

    judge = LocalJudge()

    for warning in judgeenv.startup_warnings:
        print ansi_style('#ansi[Warning: %s](yellow)' % warning)
    del judgeenv.startup_warnings
    print

    for command in [ListProblemsCommand, ListSubmissionsCommand, SubmitCommand, ResubmitCommand, RejudgeCommand,
                    DifferenceCommand, ShowCommand, HelpCommand, QuitCommand]:
        register(command(judge))

    with judge:
        try:
            judge.listen()

            while True:
                command = raw_input(ansi_style("#ansi[dmoj](magenta)#ansi[>](green) ")).strip()

                line = command.split(' ')
                if line[0] in commands:
                    cmd = commands[line[0]]
                    try:
                        cmd.execute(line[1:])
                    except InvalidCommandException as e:
                        if e.message:
                            print ansi_style("#ansi[%s](red|bold)\n" % e.message)
                        print
                else:
                    print ansi_style('#ansi[Unrecognized command %s](red|bold)' % line[0])
                    print
        except (EOFError, KeyboardInterrupt):
            print
        finally:
            judge.murder()


if __name__ == '__main__':
    sys.exit(main())
