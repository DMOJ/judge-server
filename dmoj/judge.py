#!/usr/bin/python
import os
import sys
import threading
import traceback

from dmoj import packet, graders
from dmoj.config import Problem, InvalidInitException, BatchedTestCase
from dmoj.judgeenv import env, get_problem_roots, fs_encoding
from dmoj.result import Result
from dmoj.utils.ansi import ansi_style

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print>> sys.stderr, 'No Watchdog!'
    Observer = None


    class FileSystemEventHandler(object):
        pass


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
        self.current_grader = None
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
                if os.access(os.path.join(dir, problem, 'init.yml'), os.R_OK):
                    problems.append((problem, os.path.getmtime(os.path.join(dir, problem))))
        return problems

    def update_problems(self):
        """
        Pushes current problem set to server.
        """
        self.packet_manager.supported_problems_packet(self.supported_problems())

    def begin_grading(self, id, problem_id, language, source_code, time_limit, memory_limit, short_circuit):
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
            if self.current_grader:
                self.current_grader.terminate()
            self.current_submission_thread.join()
            self.current_submission_thread = None

    def _begin_grading(self, problem_id, language, source, time_limit, memory_limit, short_circuit):
        submission_id = self.current_submission
        print ansi_style('Start grading #ansi[%s](yellow)/#ansi[%s](green|bold) in %s...'
                         % (problem_id, submission_id, language))

        try:
            problem = Problem(problem_id, time_limit, memory_limit)
        except InvalidInitException:
            traceback.print_exc()
            self.packet_manager.internal_error_packet(traceback.format_exc())
            return

        if 'grader' in problem.config:
            grader_class = graders.InteractiveGrader
        elif 'handler' in problem.config:
            grader_class = graders.SignatureGrader
        elif 'custom_judge' in problem.config:
            grader_class = graders.CustomGrader
        else:
            grader_class = graders.StandardGrader

        if isinstance(source, unicode):
            source = source.encode('utf-8')

        try:
            grader = self.current_grader = grader_class(self, problem, language, source)
        except:  # if custom grader failed to initialize, report it to the site
            traceback.print_exc()
            self.packet_manager.internal_error_packet(traceback.format_exc())
            return

        binary = grader.binary
        if not binary:
            return

        self.packet_manager.begin_grading_packet()
        try:
            for case_number, result in enumerate(self.grade_cases(grader, problem.cases,
                                                                  short_circuit=short_circuit)):
                if isinstance(result, BatchBegin):
                    self.packet_manager.batch_begin_packet()
                elif isinstance(result, BatchEnd):
                    self.packet_manager.batch_end_packet()
                else:
                    codes = result.readable_codes()
                    format_data = (case_number + 1, codes[0], Result.COLORS_BYID[codes[0]],
                                   result.execution_time, result.max_memory,
                                   '(#ansi[%s](|underline)) ' % result.feedback if result.feedback else '',
                                   '{%s}' % ', '.join(map(lambda x: '#ansi[%s](%s|bold)' % (x, Result.COLORS_BYID[x]),
                                                          codes[1:])) if len(codes) > 1 else '')
                    print ansi_style('Test case %2d #ansi[%-3s](%s|bold) [%.3fs | %dkb] %s%s' % format_data)

                    self.packet_manager.test_case_status_packet(
                        case_number + 1, result.points, result.case.points, result.result_flag, result.execution_time,
                        result.max_memory,
                        result.proc_output[:result.case.output_prefix_length].decode('utf-8', 'replace'),
                        result.feedback)
        except TerminateGrading:
            self.packet_manager.submission_terminated_packet()
            print 'Forcefully terminating grading. Temporary files may not be deleted.'
            pass
        except:
            traceback.print_exc()
            self.packet_manager.internal_error_packet(traceback.format_exc())
        else:
            self.packet_manager.grading_end_packet()
        finally:
            print ansi_style('Done grading #ansi[%s](yellow)/#ansi[%s](green|bold).' % (problem_id, submission_id))
            print
            self._terminate_grading = False
            self.current_submission_thread = None
            self.current_submission = None

    def grade_cases(self, grader, cases, short_circuit=False):
        binary = grader.binary

        # Whether we're set to skip all cases, is set to True on WA in batch
        is_short_circuiting = False

        for case in cases:
            # Stop grading if we're short circuiting
            if is_short_circuiting:
                result = Result()
                result.case = case
                result.result_flag = Result.SC
                yield result
                continue

            # Yield notifying objects for batch begin/end, and unwrap all cases inside the batches
            if isinstance(case, BatchedTestCase):
                yield BatchBegin()
                for _ in self.grade_cases(grader, case.batched_cases, short_circuit=True):
                    yield _
                yield BatchEnd()
                continue

            # Must check here because we might be interrupted mid-execution
            # If we don't bail out, we get an IR.
            # In Java's case, all the code after this will crash.
            if self._terminate_grading:
                raise TerminateGrading()

            result = grader.grade(case)

            if (result.result_flag & Result.WA) > 0 and short_circuit:
                is_short_circuiting = True

            yield result

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
    import logging
    from dmoj import judgeenv, executors

    judgeenv.load_env()

    if os.name == 'nt' and not judgeenv.no_ansi_emu:
        try:
            from colorama import init
            init()
        except ImportError as ignored:
            pass

    executors.load_executors()

    print
    print 'Running live judge...'
    print

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
