#!/usr/bin/python
from collections import OrderedDict
from textwrap import dedent
from config import Problem, InvalidInitException, BatchedTestCase
from executors.base_executor import CompiledExecutor

import judgeenv

from functools import partial
import os
import traceback
import threading
import sys
from result import Result

from judgeenv import env, get_problem_roots, fs_encoding

if os.name == 'nt':
    import ctypes

    ctypes.windll.kernel32.SetErrorMode(0x8000 | 0x0002 | 0x0004 | 0x0001)

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print>> sys.stderr, 'No Watchdog!'
    Observer = None

    class FileSystemEventHandler(object):
        pass

from error import CompileError
from communicate import safe_communicate, OutputLimitExceeded

from executors import executors
import packet
import re

try:
    import ansi2html

    def format_ansi(s):
        return ansi2html.Ansi2HTMLConverter(inline=True).convert(s, full=False)
except ImportError:
    def format_ansi(s):
        escape = OrderedDict([
            ('&', '&amp;'),
            ('<', '&lt;'),
            ('>', '&gt;'),
        ])
        for a, b in escape.items():
            s = s.replace(a, b)

        # http://stackoverflow.com/questions/13506033/filtering-out-ansi-escape-sequences
        return re.sub(r'\x1b\[([0-9,A-Z]{1,2}(;[0-9]{1,2})?(;[0-9]{3})?)?[m|K]?', '', s)


class CheckerResult(object):
    def __init__(self, passed, points, feedback=None):
        self.passed = passed
        self.points = points
        self.feedback = feedback


class BatchBegin(object):
    pass


class BatchEnd(object):
    pass


class TerminateGrading(Exception):
    pass


class SendProblemsHandler(FileSystemEventHandler):
    def __init__(self, judge):
        self.judge = judge

    def on_any_event(self, event):
        self.judge.update_problems()


class Judge(object):
    def __init__(self, **kwargs):
        self.current_submission = None
        self.current_proc = None
        self.current_submission_thread = None
        self._terminate_grading = False
        if Observer is not None:
            handler = SendProblemsHandler(self)
            self._monitor = monitor = Observer()
            for dir in get_problem_roots():
                monitor.schedule(handler, dir, recursive=True)
            monitor.start()
        else:
            self._monitor = None

    def _stop_monitor(self):
        if self._monitor is not None:
            self._monitor.stop()
            self._monitor.join(1)

    def supported_problems(self):
        """
        Fetches a list of all problems supported by this judge.
        :return:
            A list of all problems in tuple format: (problem id, mtime)
        """
        problems = []
        for dir in get_problem_roots():
            for problem in os.listdir(dir):
                if isinstance(problem, str):
                    problem = problem.decode(fs_encoding)
                if any(os.access(os.path.join(dir, problem, 'init.%s' % ext), os.R_OK) for ext in
                       ['json', 'yml', 'yaml']):
                    problems.append((problem, os.path.getmtime(os.path.join(dir, problem))))
        return problems

    def update_problems(self):
        """
        Pushes current problem set to server.
        """
        self.packet_manager.supported_problems_packet(self.supported_problems())

    def begin_grading(self, id, problem_id, language, source_code, time_limit, memory_limit, short_circuit):

        print 'Grading %s in %s...' % (problem_id, language)
        try:
            self.current_submission_thread.join()
        except AttributeError:
            pass
        self.current_submission = id
        self.current_submission_thread = threading.Thread(target=self._begin_grading,
                                                          args=(problem_id, language, source_code,
                                                                time_limit, memory_limit, short_circuit))
        self.current_submission_thread.daemon = True
        self.current_submission_thread.start()

    def terminate_grading(self):
        """
        Forcefully terminates the current submission. Not necessarily safe.
        """
        if self.current_submission_thread:
            self._terminate_grading = True
            if self.current_proc:
                try:
                    self.current_proc.kill()
                except OSError:
                    pass
            self.current_submission_thread.join()
            self.current_submission_thread = None

    def _begin_grading(self, problem_id, language, original_source, time_limit, memory_limit, short_circuit):
        submission_id = self.current_submission

        binary = self.generate_binary(problem_id, language, original_source)
        if not binary:
            return

        try:
            problem = Problem(problem_id)
        except InvalidInitException:
            traceback.print_exc()
            self.packet_manager.internal_error_packet(traceback.format_exc())
            self._end_grading()
            return

        try:
            for case_number, case_data in enumerate(self.grade_cases(binary, problem.cases, time_limit, memory_limit,
                                                                     short_circuit=short_circuit)):
                if isinstance(case_data, BatchBegin):
                    self.packet_manager.batch_begin_packet()
                elif isinstance(case_data, BatchEnd):
                    self.packet_manager.batch_end_packet()
                else:
                    case, result, check, feedback = case_data
                    codes = result.readable_codes()
                    print 'Test case %d %s [%.3fs | %dkb] %s%s' % (case_number + 1,
                                                                   codes[0],
                                                                   result.execution_time,
                                                                   result.max_memory,
                                                                   '(%s) ' % feedback if feedback else '',
                                                                   '{%s}' % ', '.join(codes[1:]) if len(
                                                                       codes) > 1 else '')
                    self.packet_manager.test_case_status_packet(
                        case_number, check.points, case.points, result.result_flag, result.execution_time,
                        result.max_memory,
                        result.proc_output[:case.output_prefix_length].decode('utf-8', 'replace'), feedback)
        except TerminateGrading:
            self.packet_manager.submission_terminated_packet()
            print 'Forcefully terminating grading. Temporary files may not be deleted.'
            pass
        except:
            traceback.print_exc()
            self.packet_manager.internal_error_packet(traceback.format_exc())
        finally:
            print '===========Done Grading: %s===========' % submission_id
            self._terminate_grading = False
            self.current_submission_thread = None
            self.current_submission = None
            self.packet_manager.grading_end_packet()

    def generate_binary(self, problem_id, language, original_source):

        # If the executor requires compilation, compile and send any errors/warnings to the site
        executor = executors[language].Executor
        if issubclass(executor, CompiledExecutor):
            try:
                # Fetch an appropriate executor for the language
                binary = executor(problem_id, original_source)
            except CompileError as compilation_error:
                self.packet_manager.compile_error_packet(compilation_error.message)
                self._end_grading()

                # Compile error is fatal
                return None
        else:
            binary = executor(problem_id, original_source)

        # Carry on grading in case of compile warning
        if hasattr(binary, 'warning') and binary.warning:
            self.packet_manager.compile_message_packet(format_ansi(binary.warning))
        return binary

    def grade_cases(self, binary, cases, time_limit, memory_limit, short_circuit=False):
        is_short_circuiting = False
        for case in cases:
            result = Result()
            feedback = None
            check = CheckerResult(False, 0)
            if is_short_circuiting:
                result.result_flag = Result.SC
            else:

                if isinstance(case, BatchedTestCase):
                    yield BatchBegin()
                    for _ in self.grade_cases(binary, case.batched_cases, time_limit, memory_limit, short_circuit=True):
                        yield _
                    yield BatchEnd()
                    continue

                process = binary.launch(time=time_limit, memory=memory_limit, pipe_stderr=True,
                                        unbuffered=case.config.unbuffered)
                self.current_proc = process

                # Assume AC unless proven otherwise

                communicate = process.safe_communicate if hasattr(process, 'safe_communicate') else \
                    partial(safe_communicate, process)

                try:
                    result.proc_output, error = communicate(case.input_data(), outlimit=25165824, errlimit=1048576)
                except OutputLimitExceeded as ole:
                    stream, result.proc_output, error = ole.args
                    print 'OLE:', stream
                    result.result_flag |= Result.OLE
                    process.kill()
                    process.wait()
                if error:
                    sys.stderr.write(error)

                # Must check here because we might be interrupted mid-execution
                # If we don't bail out, we get an IR.
                # In Java's case, all the code after this will crash.
                if self._terminate_grading:
                    raise TerminateGrading()

                result.max_memory = process.max_memory or 0.0
                result.execution_time = process.execution_time or 0.0
                result.r_execution_time = process.r_execution_time or 0.0

                # C standard checker will crash if not given a string
                proc_output = result.proc_output or ''

                check = case.checker()(proc_output, case.output_data(),
                                       submission_source=binary.source,
                                       judge_input=case.input_data(),
                                       point_value=case.points)

                # checkers must either return a boolean (True: full points, False: 0 points)
                # or a CheckerResult, so convert to CheckerResult if it returned bool
                if not isinstance(check, CheckerResult):
                    check = CheckerResult(check, case.points if check else 0.0)

                if not check.passed:
                    result.result_flag |= Result.WA
                    if short_circuit:
                        is_short_circuiting = True
                else:
                    result.result_flag |= Result.AC

                feedback = (check.feedback or
                            (process.feedback if hasattr(process, 'feedback') else
                             getattr(binary, 'get_feedback', lambda x, y: '')(error, result)))

            yield case, result, check, feedback

    def _end_grading(self):
        # self.packet_manager.grading_end_packet()
        pass

    def listen(self):
        """
        Attempts to connect to the handler server specified in command line.
        """
        self.packet_manager.run()

    def __del__(self):
        self._stop_monitor()
        del self.packet_manager

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        pass

    def murder(self):
        """
        End any submission currently executing, and exit the judge.
        """
        self.terminate_grading()
        self._stop_monitor()


class ClassicJudge(Judge):
    def __init__(self, host, port, **kwargs):
        self.packet_manager = packet.PacketManager(host, port, self, env['id'], env['key'])
        super(ClassicJudge, self).__init__(**kwargs)


class AMQPJudge(Judge):
    def __init__(self, url, **kwargs):
        self.packet_manager = packet.AMQPPacketManager(self, url, env['id'], env['key'])
        super(AMQPJudge, self).__init__(**kwargs)


def main():
    print 'Running live judge...'

    import logging

    logging.basicConfig(filename=judgeenv.log_file, level=logging.INFO,
                        format='%(levelname)s %(asctime)s %(module)s %(message)s')

    if judgeenv.server_host.startswith(('amqp://', 'amqps://')):
        judge = AMQPJudge(judgeenv.server_host)
    else:
        judge = ClassicJudge(judgeenv.server_host, judgeenv.server_port)

    with judge:
        try:
            judge.listen()
        finally:
            judge.murder()


if __name__ == '__main__':
    main()
