#!/usr/bin/python
import errno
import logging
import os
import signal
import sys
import threading
import traceback
from http.server import HTTPServer
from itertools import chain

from dmoj import graders, packet
from dmoj.control import JudgeControlRequestHandler
from dmoj.error import CompileError
from dmoj.judgeenv import clear_problem_dirs_cache, env, get_supported_problems, startup_warnings
from dmoj.monitor import DummyMonitor, Monitor
from dmoj.problem import BatchedTestCase, Problem
from dmoj.result import Result
from dmoj.utils.ansi import ansi_style, print_ansi, strip_ansi
from dmoj.utils.unicode import unicode_stdout_stderr, utf8bytes, utf8text

try:
    import readline  # noqa: F401, imported for the side-effect of making `input()` have readline.
except ImportError:
    pass

try:
    from setproctitle import setproctitle
except ImportError:
    def setproctitle(title):
        pass


class BatchBegin:
    pass


class BatchEnd:
    pass


class TerminateGrading(Exception):
    pass


class Judge:
    def __init__(self):
        self.current_grader = None
        self.current_submission_id = None
        self.current_submission_thread = None
        self._terminate_grading = False
        self.packet_manager = None

        self.updater_exit = False
        self.updater_signal = threading.Event()
        self.updater = threading.Thread(target=self._updater_thread)

    def _updater_thread(self):
        log = logging.getLogger('dmoj.updater')
        while True:
            self.updater_signal.wait()
            self.updater_signal.clear()
            if self.updater_exit:
                return

            # Prevent problem updates while grading.
            # Capture the value so it can't change.
            thread = self.current_submission_thread
            if thread:
                thread.join()

            try:
                clear_problem_dirs_cache()
                self.packet_manager.supported_problems_packet(get_supported_problems())
            except Exception:
                log.exception('Failed to update problems.')

    def update_problems(self):
        """
        Pushes current problem set to server.
        """
        self.updater_signal.set()

    def _block_and_grade(self, problem, language, source, short_circuit, meta, report=print):
        if 'signature_grader' in problem.config:
            grader_class = graders.SignatureGrader
        elif 'interactive' in problem.config:
            grader_class = graders.BridgedInteractiveGrader
        elif 'custom_judge' in problem.config:
            grader_class = graders.CustomGrader
        else:
            grader_class = graders.StandardGrader

        try:
            self.current_grader = grader_class(self, problem, language, utf8bytes(source), meta)
        except CompileError as compilation_error:
            error = compilation_error.args[0] or b'compiler exited abnormally'

            report(ansi_style('#ansi[Failed compiling submission!](red|bold)'))
            report(error.rstrip())  # don't print extra newline

            self.packet_manager.compile_error_packet(error)
            return
        else:
            binary = self.current_grader.binary
            if hasattr(binary, 'warning') and binary.warning is not None:
                self.packet_manager.compile_message_packet(binary.warning)

        self.packet_manager.begin_grading_packet(self.current_grader.is_pretested)

        batch_counter = 1
        in_batch = False

        # cases are indexed at 1
        case_number = 1
        try:
            for result in self.grade_cases(self.current_grader, self.current_grader.cases(),
                                           short_circuit=short_circuit):
                if isinstance(result, BatchBegin):
                    self.packet_manager.batch_begin_packet()
                    report(ansi_style("#ansi[Batch #%d](yellow|bold)" % batch_counter))
                    in_batch = True
                elif isinstance(result, BatchEnd):
                    self.packet_manager.batch_end_packet()
                    batch_counter += 1
                    in_batch = False
                else:
                    codes = result.readable_codes()

                    # here be cancer
                    is_sc = (result.result_flag & Result.SC)
                    colored_codes = list(map(lambda x: '#ansi[%s](%s|bold)' % ('--' if x == 'SC' else x,
                                                                               Result.COLORS_BYID[x]), codes))
                    colored_aux_codes = '{%s}' % ', '.join(colored_codes[1:]) if len(codes) > 1 else ''
                    colored_feedback = '(#ansi[%s](|underline)) ' % utf8text(result.feedback) if result.feedback else ''
                    case_info = '[%.3fs (%.3fs) | %dkb] %s%s' % (result.execution_time,
                                                                 result.wall_clock_time,
                                                                 result.max_memory,
                                                                 colored_feedback,
                                                                 colored_aux_codes) if not is_sc else ''
                    case_padding = '  ' * in_batch
                    report(ansi_style('%sTest case %2d %-3s %s' % (case_padding, case_number,
                                                                   colored_codes[0], case_info)))

                    self.packet_manager.test_case_status_packet(case_number, result)

                    case_number += 1
        except TerminateGrading:
            self.packet_manager.submission_terminated_packet()
            report(ansi_style('#ansi[Forcefully terminating grading. '
                              'Temporary files may not be deleted.](red|bold)'))
            pass
        else:
            self.packet_manager.grading_end_packet()

    def begin_grading(self, id, problem_id, language, source, time_limit, memory_limit, short_circuit, meta,
                      report=print, blocking=False):
        self.current_submission_id = id

        def grading_cleanup_wrapper():
            report(ansi_style('Start grading #ansi[%s](yellow)/#ansi[%s](green|bold) in %s...'
                              % (problem_id, id, language)))

            try:
                problem = Problem(problem_id, time_limit, memory_limit)
                self._block_and_grade(problem, language, source, short_circuit, meta, report=report)
            except Exception:
                self.log_internal_error()

            self._terminate_grading = False
            self.current_submission_id = None
            self.current_submission_thread = None
            self.current_grader = None
            report(ansi_style('Done grading #ansi[%s](yellow)/#ansi[%s](green|bold).\n' % (problem_id, id)))

        self.current_submission_thread = threading.Thread(target=grading_cleanup_wrapper)
        self.current_submission_thread.daemon = True
        self.current_submission_thread.start()

        # Submission may have been killed already, but block if it hasn't been.
        if blocking and self.current_submission_thread is not None:
            self.current_submission_thread.join()

    def grade_cases(self, grader, cases, short_circuit=False, is_short_circuiting=False):
        for case in cases:
            # Yield notifying objects for batch begin/end, and unwrap all cases inside the batches
            if isinstance(case, BatchedTestCase):
                yield BatchBegin()

                for batched_case in self.grade_cases(grader, case.batched_cases,
                                                     short_circuit=case.config['short_circuit'],
                                                     is_short_circuiting=is_short_circuiting):
                    # A batched case just failed.
                    # There are two cases where this means that we should completely short-circuit:
                    # 1. If the batch was worth 0 points, to emulate the property of 0-point cases.
                    # 2. If the short_circuit flag is true, see <https://github.com/DMOJ/judge/issues/341>.
                    if (batched_case.result_flag & Result.WA) and (not case.points or short_circuit):
                        is_short_circuiting = True
                    yield batched_case
                yield BatchEnd()
                continue

            # Stop grading if we're short circuiting
            if is_short_circuiting:
                result = Result(case)
                result.result_flag = Result.SC
                yield result
                continue

            result = grader.grade(case)

            # If the submission was killed due to an user-initiated abort, any result is meaningless.
            if self._terminate_grading:
                raise TerminateGrading()

            # If the WA bit of result_flag is set and we are set to short-circuit (e.g., in a batch),
            # short circuit the rest of the cases.
            # Do the same if the case is a pretest (i.e. has 0 points)
            if (result.result_flag & Result.WA) > 0 and (short_circuit or not case.points):
                is_short_circuiting = True

            yield result

    def log_internal_error(self, exc=None):
        # If exc is exists, raise it so that sys.exc_info() is populated with its data
        if exc:
            try:
                raise exc
            except:  # noqa: E722, we want to catch everything
                pass
        exc = sys.exc_info()

        message = ''.join(traceback.format_exception(*exc))

        # Strip ANSI from the message, since this might be a checker's CompileError
        # ...we don't want to see the raw ANSI codes from GCC/Clang on the site.
        # We could use format_ansi and send HTML to the site, but the site doesn't presently support HTML
        # internal error formatting.
        self.packet_manager.internal_error_packet(strip_ansi(message))

        # Logs can contain ANSI, and it'll display fine
        print(message, file=sys.stderr)

    def terminate_grading(self):
        """
        Forcefully terminates the current submission. Not necessarily safe.
        """
        if self.current_submission_thread:
            self._terminate_grading = True
            if self.current_grader:
                self.current_grader.terminate_grading()
            self.current_submission_thread.join()
            self.current_submission_thread = None

    def listen(self):
        """
        Attempts to connect to the handler server specified in command line.
        """
        self.updater.start()
        self.packet_manager.run()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        pass

    def murder(self):
        """
        End any submission currently executing, and exit the judge.
        """
        self.terminate_grading()
        self.updater_exit = True
        self.updater_signal.set()
        if self.packet_manager:
            self.packet_manager.close()


class ClassicJudge(Judge):
    def __init__(self, host, port, **kwargs):
        super().__init__()
        self.packet_manager = packet.PacketManager(host, port, self, env['id'], env['key'], **kwargs)


def sanity_check():
    if os.name == 'nt':
        print('cannot run judge on Windows', file=sys.stderr)
        return False
    else:
        # Don't allow starting up without cptbox, saves cryptic errors later on
        try:
            from .cptbox import _cptbox  # noqa: F401, we want to see if this imports
        except ImportError:
            print('cptbox must be compiled to grade!', file=sys.stderr)
            return False

        # However running as root on Linux is a Bad Idea
        if os.getuid() == 0:
            startup_warnings.append('running the judge as root can be potentially unsafe, '
                                    'consider using an unprivileged user instead')

        # Our sandbox filter is long but simple, so we can see large improvements
        # in overhead by enabling the BPF JIT for seccomp.
        bpf_jit_path = '/proc/sys/net/core/bpf_jit_enable'
        if os.path.exists(bpf_jit_path):
            with open(bpf_jit_path, 'r') as f:
                if f.read().strip() != '1':
                    startup_warnings.append('running without BPF JIT enabled, consider running '
                                            '`echo 1 > /proc/sys/net/core/bpf_jit_enable` '
                                            'to reduce sandbox overhead')

    # _checker implements standard checker functions in C
    # we fall back to a Python implementation if it's not compiled, but it's slower
    try:
        from .checkers import _checker  # noqa: F401, we want to see if this imports
    except ImportError:
        startup_warnings.append('native checker module not found, compile _checker for optimal performance')
    return True


def make_host_port(judgeenv):
    host = judgeenv.server_host
    if ':' in host:
        host = '[%s]' % (host,)
    return '%s:%s%s' % (host, judgeenv.server_port, 's' if judgeenv.secure else '')


def judge_proc(need_monitor):
    from dmoj import judgeenv

    logfile = judgeenv.log_file

    try:
        logfile = logfile % env['id']
    except TypeError:
        pass

    logging.basicConfig(filename=logfile, level=logging.INFO,
                        format='%(levelname)s %(asctime)s %(process)d %(module)s %(message)s')

    setproctitle('DMOJ Judge: %s on %s' % (env['id'], make_host_port(judgeenv)))

    judge = ClassicJudge(judgeenv.server_host, judgeenv.server_port,
                         secure=judgeenv.secure, no_cert_check=judgeenv.no_cert_check,
                         cert_store=judgeenv.cert_store)
    if need_monitor:
        monitor = Monitor()
        monitor.callback = judge.update_problems
    else:
        monitor = DummyMonitor()

    if hasattr(signal, 'SIGUSR2'):
        def update_problem_signal(signum, frame):
            judge.update_problems()

        signal.signal(signal.SIGUSR2, update_problem_signal)

    if need_monitor and judgeenv.api_listen:
        judge_instance = judge

        class Handler(JudgeControlRequestHandler):
            judge = judge_instance

        api_server = HTTPServer(judgeenv.api_listen, Handler)
        thread = threading.Thread(target=api_server.serve_forever)
        thread.daemon = True
        thread.start()
    else:
        api_server = None

    print()
    with monitor, judge:
        try:
            judge.listen()
        except Exception:
            traceback.print_exc()
        finally:
            judge.murder()
            if api_server:
                api_server.shutdown()


PR_SET_PDEATHSIG = 1

logpm = logging.getLogger('dmoj.judgepm')


class JudgeManager:
    signal_map = {k: v for v, k in sorted(signal.__dict__.items(), reverse=True)
                  if v.startswith('SIG') and not v.startswith('SIG_')}

    def __init__(self, judges):
        self.libc = self.__get_libc()
        self.prctl = self.libc.prctl

        self._try_respawn = True
        self.auth = {entry.id: entry.key for entry in judges}
        self.orig_signal = {}

        self.master_pid = os.getpid()
        self.pids = {}
        self.monitor_pid = None
        self.api_pid = None

        self.monitor = Monitor()

    def __get_libc(self):
        from ctypes.util import find_library
        from ctypes import CDLL
        return CDLL(find_library('c'))

    def _forward_signal(self, sig, respawn=False):
        def handler(signum, frame):
            # SIGUSR2, the signal for file updates, may be triggered very quickly.
            # Due to processing delays, it may cause reentrancy issues when logging.
            # Band-aid fix is to avoid logging SIGUSR2.
            if signum not in (signal.SIGUSR2,):
                logpm.info('Received signal (%s), forwarding...', self.signal_map.get(signum, signum))
                if not respawn:
                    logpm.info('Will no longer respawn judges.')
                    self._try_respawn = False
            self.signal_all(signum)

        self.orig_signal[sig] = signal.signal(sig, handler)

    def _spawn_child(self, func, *args, **kwargs):
        sys.stdout.flush()
        sys.stderr.flush()
        ppid = os.getpid()

        # Pipe to signal signal handler initialization.
        pr, pw = os.pipe()
        try:
            pid = os.fork()
        except OSError:
            logpm.exception('Failed to spawn child process.')
            return
        if pid == 0:
            # In child. Scary business.
            self.prctl(PR_SET_PDEATHSIG, signal.SIGTERM)
            if ppid != os.getppid():
                os.kill(os.getpid(), signal.SIGTERM)
                os._exit(2)
            sys.stdin.close()
            os.close(pr)

            for sig, handler in self.orig_signal.items():
                signal.signal(sig, handler)
            os.close(pw)

            # How could we possibly return to top level?
            try:
                os._exit(func(*args, **kwargs) or 0)
            finally:
                os._exit(1)  # If that os._exit fails because ret is a truthy non-int, then this will ensure death.

        # In parent.
        os.close(pw)

        # Block until child initializes signals before we register this child to receive signals.
        while True:
            try:
                os.read(pr, 1)
            except OSError as e:
                if e.errno != errno.EINTR:
                    raise
            else:
                break
        os.close(pr)
        return pid

    def _judge_proc(self, id):
        env['id'] = id
        env['key'] = self.auth[id]
        try:
            return judge_proc(False)
        except BaseException:
            return 1
        finally:
            sys.stdout.flush()
            sys.stderr.flush()
            logging.shutdown()

    def _spawn_judge(self, id):
        pid = self._spawn_child(self._judge_proc, id)
        self.pids[pid] = id
        logpm.info('Judge %s is pid %d', id, pid)

    def _spawn_monitor(self):
        def monitor_proc():
            setproctitle('DMOJ Judge: File monitor')
            signal.signal(signal.SIGUSR2, signal.SIG_IGN)

            event = threading.Event()
            stop = False

            def worker():
                while True:
                    event.wait()
                    event.clear()
                    if stop:
                        return
                    event.wait(1)
                    if event.is_set():
                        continue
                    os.kill(self.master_pid, signal.SIGUSR2)

            threading.Thread(target=worker).start()
            self.monitor.callback = event.set
            self.monitor.start()
            try:
                self.monitor.join()
            except KeyboardInterrupt:
                self.monitor.stop()
                stop = True
                event.set()

        self.monitor_pid = self._spawn_child(monitor_proc)
        logpm.info('Monitor is pid %d', self.monitor_pid)

    def _spawn_api(self):
        from dmoj import judgeenv

        master_pid = self.master_pid

        class Handler(JudgeControlRequestHandler):
            def update_problems(self):
                os.kill(master_pid, signal.SIGUSR2)

        server = HTTPServer(judgeenv.api_listen, Handler)

        def api_proc():
            setproctitle('DMOJ Judge: API server')
            signal.signal(signal.SIGUSR2, signal.SIG_IGN)
            server.serve_forever()

        self.api_pid = self._spawn_child(api_proc)
        logpm.info('API server is pid %d', self.api_pid)

    def _spawn_all(self):
        from dmoj import judgeenv

        for id in self.auth:
            logpm.info('Spawning judge: %s', id)
            self._spawn_judge(id)
        if self.monitor.is_real:
            logpm.info('Spawning monitor')
            self._spawn_monitor()
        if judgeenv.api_listen is not None:
            logpm.info('Spawning API server')
            self._spawn_api()

    def _monitor(self):
        while self._try_respawn or self.pids:
            try:
                pid, status = os.wait()
            except (OSError, IOError) as e:
                if e.errno == errno.EINTR:
                    continue
                raise
            if not os.WIFSIGNALED(status) and not os.WIFEXITED(status):
                continue
            if pid in self.pids:
                # A child just died.
                judge = self.pids[pid]
                del self.pids[pid]
                if self._try_respawn:
                    logpm.warning('Judge died, respawning: %s (pid %d, 0x%08X)', judge, pid, status)
                    self._spawn_judge(judge)
                else:
                    logpm.info('Judge exited: %s (pid %d, 0x%08X)', judge, pid, status)
            elif pid == self.monitor_pid:
                if self._try_respawn:
                    logpm.warning('Monitor died, respawning (0x%08X)', status)
                    self._spawn_monitor()
                else:
                    logpm.info('Monitor exited: (0x%08X)', status)
            elif pid == self.api_pid:
                if self._try_respawn:
                    logpm.warning('API server died, respawning (0x%08X)', status)
                    self._spawn_api()
                else:
                    logpm.info('API server exited: (0x%08X)', status)
            else:
                logpm.error('I am not your father, %d (0x%08X)!', pid, status)

    def _respawn_judges(self, signum, frame):
        logpm.info('Received signal (%s), murderizing all children.', self.signal_map.get(signum, signum))
        self.signal_all(signal.SIGTERM)

    def run(self):
        logpm.info('Starting process manager: %d.', os.getpid())

        from dmoj import judgeenv
        setproctitle('DMOJ Judge: Process manager on %s' % (make_host_port(judgeenv),))

        self._forward_signal(signal.SIGUSR2, respawn=True)
        self._forward_signal(signal.SIGINT)
        self._forward_signal(signal.SIGQUIT)
        self._forward_signal(signal.SIGTERM)
        signal.signal(signal.SIGHUP, self._respawn_judges)

        self._spawn_all()
        try:
            self._monitor()
        except KeyboardInterrupt:
            self._try_respawn = False
            self.signal_all(signal.SIGINT)
            self._monitor()

        logpm.info('Exited gracefully: %d.', os.getpid())

    def signal_all(self, signum):
        for pid in chain(self.pids, [self.monitor_pid, self.api_pid]):
            if pid is None:
                continue
            try:
                os.kill(pid, signum)
            except OSError as e:
                if e.errno != errno.ESRCH:
                    raise
                    # Well the monitor will catch on eventually if the process vanishes.


def main():  # pragma: no cover
    unicode_stdout_stderr()

    if not sanity_check():
        return 1

    from dmoj import judgeenv, executors

    judgeenv.load_env()

    executors.load_executors()

    if hasattr(signal, 'SIGUSR2'):
        signal.signal(signal.SIGUSR2, signal.SIG_IGN)

    print('Running live judge...')

    for warning in judgeenv.startup_warnings:
        print_ansi('#ansi[Warning: %s](yellow)' % warning)
    del judgeenv.startup_warnings

    if 'judges' in env:
        logfile = judgeenv.log_file
        try:
            logfile = logfile % 'master'
        except TypeError:
            pass
        logging.basicConfig(filename=logfile, level=logging.INFO,
                            format='%(levelname)s %(asctime)s %(process)d %(name)s %(message)s')
        if env.pidfile:
            with open(env.pidfile) as f:
                f.write(str(os.getpid()))
        manager = JudgeManager(env.judges)
        manager.run()
    else:
        return judge_proc(need_monitor=True)


if __name__ == '__main__':
    main()
