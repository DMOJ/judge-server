#!/usr/bin/python
import os
import sys
import threading
import traceback

from dmoj import packet, graders
from dmoj.config import Problem, InvalidInitException, BatchedTestCase
from dmoj.error import CompileError
from dmoj.judgeenv import env, get_problem_roots, get_supported_problems, startup_warnings
from dmoj.result import Result
from dmoj.utils.ansi import ansi_style

if os.name == 'posix':
    try:
        import readline
    except ImportError:
        pass

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    startup_warnings.append('watchdog module not found, install it to automatically update problems')
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
    def __init__(self):
        global startup_warnings
        self.current_submission = None
        self.current_grader = None
        self.current_submission_thread = None
        self._terminate_grading = False
        if Observer is not None:
            handler = SendProblemsHandler(self)
            self._monitor = monitor = Observer()
            for dir in get_problem_roots():
                monitor.schedule(handler, dir, recursive=True)
            try:
                monitor.start()
            except OSError:
                startup_warnings.append('failed to start filesystem monitor')
                self._monitor = None
        else:
            self._monitor = None

    def _stop_monitor(self):
        if self._monitor is not None:
            self._monitor.stop()
            self._monitor.join(1)

    def update_problems(self):
        """
        Pushes current problem set to server.
        """
        self.packet_manager.supported_problems_packet(get_supported_problems())

    def begin_grading(self, id, problem_id, language, source_code, time_limit, memory_limit, short_circuit,
                      blocking=False):
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
        if blocking:
            self.current_submission_thread.join()

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
            return self.internal_error()

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
            grader = grader_class(self, problem, language, source)
        except CompileError as ce:
            print ansi_style('#ansi[Failed compiling submission!](red|bold)')
            print ce.message,  # don't print extra newline
            grader = None
        except:  # if custom grader failed to initialize, report it to the site
            return self.internal_error()

        binary = grader.binary if grader else None

        # the compiler may have failed, or an error could have happened while initializing a custom judge
        # either way, we can't continue
        if binary:
            self.packet_manager.begin_grading_packet()

            batch_counter = 1
            in_batch = False
            try:
                for case_number, result in enumerate(self.grade_cases(grader, problem.cases,
                                                                      short_circuit=short_circuit)):
                    if isinstance(result, BatchBegin):
                        self.packet_manager.batch_begin_packet()
                        print ansi_style("#ansi[Batch #%d](yellow|bold)" % batch_counter)
                        in_batch = True
                    elif isinstance(result, BatchEnd):
                        self.packet_manager.batch_end_packet()
                        batch_counter += 1
                        in_batch = False
                    else:
                        codes = result.readable_codes()

                        # here be cancer
                        is_sc = (result.result_flag & Result.SC)
                        colored_codes = map(lambda x: '#ansi[%s](%s|bold)' % ('--' if x == 'SC' else x,
                                                                              Result.COLORS_BYID[x]), codes)
                        colored_aux_codes = '{%s}' % ', '.join(colored_codes[1:]) if len(codes) > 1 else ''
                        colored_feedback = '(#ansi[%s](|underline)) ' % result.feedback if result.feedback else ''
                        case_info = '[%.3fs | %dkb] %s%s' % (result.execution_time, result.max_memory,
                                                             colored_feedback,
                                                             colored_aux_codes) if not is_sc else ''
                        case_padding = '  ' * in_batch
                        print ansi_style('%sTest case %2d %-3s %s' % (case_padding, case_number + 1,
                                                                      colored_codes[0], case_info))

                        # cases are indexed at 1
                        self.packet_manager.test_case_status_packet(
                            case_number + 1, result.points, result.case.points, result.result_flag,
                            result.execution_time,
                            result.max_memory,
                            result.proc_output[:result.case.output_prefix_length].decode('utf-8', 'replace'),
                            result.feedback)
            except TerminateGrading:
                self.packet_manager.submission_terminated_packet()
                print ansi_style('#ansi[Forcefully terminating grading. Temporary files may not be deleted.](red|bold)')
                pass
            except:
                self.internal_error()
            else:
                self.packet_manager.grading_end_packet()

        print ansi_style('Done grading #ansi[%s](yellow)/#ansi[%s](green|bold).' % (problem_id, submission_id))
        print
        self._terminate_grading = False
        self.current_submission_thread = None
        self.current_submission = None
        self.current_grader = None

    def grade_cases(self, grader, cases, short_circuit=False, is_short_circuiting=False):

        for case in cases:
            # Yield notifying objects for batch begin/end, and unwrap all cases inside the batches
            if isinstance(case, BatchedTestCase):
                yield BatchBegin()
                for _ in self.grade_cases(grader, case.batched_cases, short_circuit=True,
                                          is_short_circuiting=is_short_circuiting):
                    yield _
                yield BatchEnd()
                continue

            # Stop grading if we're short circuiting
            if is_short_circuiting:
                result = Result(case)
                result.result_flag = Result.SC
                yield result
                continue

            # Must check here because we might be interrupted mid-execution
            # If we don't bail out, we get an IR.
            # In Java's case, all the code after this will crash.
            if self._terminate_grading:
                raise TerminateGrading()

            result = grader.grade(case)

            # If the WA bit of result_flag is set and we are set to short-circuit (e.g., in a batch),
            # short circuit the rest of the cases.
            # Do the same if the case is a pretest (i.e. has 0 points)
            if (result.result_flag & Result.WA) > 0 and (short_circuit or case.points == 0):
                is_short_circuiting = True

            yield result

    def internal_error(self, exc=None):
        if exc:
            try:
                raise exc
            except:
                pass
        exc = sys.exc_info()

        traceback.print_exception(*exc)
        self.packet_manager.internal_error_packet(''.join(traceback.format_exception(*exc)))

    def listen(self):
        """
        Attempts to connect to the handler server specified in command line.
        """
        self.packet_manager.run()

    def __del__(self):
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


class ClassicJudge(Judge):
    def __init__(self, host, port):
        self.packet_manager = packet.PacketManager(host, port, self, env['id'], env['key'])
        super(ClassicJudge, self).__init__()


def sanity_check():
    # Don't allow starting up without wbox/cptbox, saves cryptic errors later on
    if os.name == 'nt':
        try:
            import wbox
        except ImportError:
            print >> sys.stderr, "wbox must be compiled to grade!"
            return False

        # DMOJ needs to be run as admin on Windows
        import ctypes
        if ctypes.windll.shell32.IsUserAnAdmin() == 0:
            print >> sys.stderr, "can't start, the DMOJ judge must be ran as admin"
            return False
    else:
        try:
            import cptbox
        except ImportError:
            print >> sys.stderr, "cptbox must be compiled to grade!"
            return False

        # However running as root on Linux is a Bad Idea
        if os.getuid() == 0:
            startup_warnings.append('running the judge as root can be potentially unsafe, '
                                    'consider using an unprivileged user instead')

    # _checker implements standard checker functions in C
    # we fall back to a Python implementation if it's not compiled, but it's slower
    try:
        from checkers import _checker
    except ImportError:
        startup_warnings.append('native checker module not found, compile _checker for optimal performance')
    return True


def main():
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
    if not sanity_check():
        return 1

    import logging
    from dmoj import judgeenv, executors

    judgeenv.load_env()

    # Emulate ANSI colors with colorama
    if os.name == 'nt' and not judgeenv.no_ansi_emu:
        try:
            from colorama import init
            init()
        except ImportError as ignored:
            pass

    executors.load_executors()

    print 'Running live judge...'

    logging.basicConfig(filename=judgeenv.log_file, level=logging.INFO,
                        format='%(levelname)s %(asctime)s %(module)s %(message)s')

    judge = ClassicJudge(judgeenv.server_host, judgeenv.server_port)

    for warning in judgeenv.startup_warnings:
        print ansi_style('#ansi[Warning: %s](yellow)' % warning)
    del judgeenv.startup_warnings
    print

    with judge:
        try:
            judge.listen()
        except:
            traceback.print_exc()
        finally:
            judge.murder()


if __name__ == '__main__':
    main()
