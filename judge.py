#!/usr/bin/python
from textwrap import dedent

import judgeenv

import copy
from functools import partial
import gc
import json
import os
import traceback
import threading
import zipfile
import cStringIO
import re
import sys
import subprocess
import uuid

from modload import load_module_from_file
from result import Result

from judgeenv import env, get_problem_root, get_problem_roots, fs_encoding

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
import checkers
import packet


class CheckerResult(object):
    def __init__(self, passed, points, feedback=None):
        self.passed = passed
        self.points = points
        self.feedback = feedback


class TestCase(object):
    def __init__(self, input_file, output_file, point_value):
        self.list = [(input_file, output_file, int(point_value))]

    def __iter__(self):
        return iter(self.list)


class BatchedTestCase(object):
    def __init__(self, io_files, point_value):
        point = int(point_value)
        self.list = [(i, o, point) for i, o in io_files]

    def __iter__(self):
        return iter(self.list)


class TerminateGrading(Exception):
    pass


class SendProblemsHandler(FileSystemEventHandler):
    def __init__(self, judge):
        self.judge = judge

    def on_any_event(self, event):
        print>> sys.stderr, event
        self.judge.update_problems()


class Judge(object):
    def __init__(self, host, port, **kwargs):
        self.packet_manager = packet.PacketManager(host, port, self, env['id'], env['key'])
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
                if os.access(os.path.join(dir, problem, 'init.json'), os.R_OK):
                    problems.append((problem, os.path.getmtime(os.path.join(dir, problem))))
        return problems

    def update_problems(self):
        """
        Pushes current problem set to server.
        """
        self.packet_manager.supported_problems_packet(self.supported_problems())

    def begin_grading(self, id, problem_id, language, source_code, time_limit, memory_limit, short_circuit):
        """
        Grades a submission.
        This method also handles notifying the server of judging results.
        :param id:
            The submission id to identify this submission with the server.
        :param problem_id: 
            Problem code.
        :param language: 
            The submission language, e.g. "CPP", "CPP11", "PY2"
        :param source_code: 
            The source code for the submission.
        :param time_limit: 
            Time limit for submission program, in seconds.
        :param memory_limit: 
            Memory limit for submission program, in kilobytes.
        :param short_circuit: 
            Whether to short-circuit batch testcases on WA.
        """
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

    def _begin_grading(self, problem_id, language, original_source, time_limit, memory_limit, short_circuit):
        """
        Threaded callback for begin_grading.
        """
        submission_id = self.current_submission
        print>> sys.stderr, '===========Started Grading: %s===========' % submission_id
        try:
            problem_root = get_problem_root(problem_id)
            if problem_root is None:
                print>>sys.stderr, 'Unsupported problem:', problem_id
                print>>sys.stderr, 'Please install watchdog so that the bridge can be notified of problems files' \
                                   ' disappearing'
                self.packet_manager.internal_error_packet(dedent('''\
                    Unsupported problem: %s.

                    Please install watchdog so that the bridge can be notified of problem files disappearing.''')
                                                          % problem_id)
                return
            with open(os.path.join(problem_root, 'init.json'), 'r') as init_file:
                init_data = json.load(init_file)

                if isinstance(original_source, unicode):
                    source_code = original_source.encode('utf-8')
                else:
                    source_code = original_source
                try:
                    # Launch an executor for the given language
                    # The executor is responsible for writing source files and compiling (if applicable)
                    if 'handler' in init_data:
                        siggraders = ('C', 'CPP', 'CPP0X', 'CPP11')

                        for i in xrange(3, -1, -1):
                            if siggraders[i] in executors:
                                siggrader = siggraders[i]
                                break
                        else:
                            raise CompileError("Can't signature grade. Why did I get this submission?")
                        if language in siggraders:
                            aux_sources = {}
                            handler_data = init_data['handler']
                            entry_path = os.path.join(problem_root, handler_data['entry'])
                            header_path = os.path.join(problem_root, handler_data['header'])

                            if not os.path.exists(entry_path):
                                raise IOError('entry path "%s" does not exist' % entry_path)
                            if not os.path.exists(header_path):
                                raise IOError('header path "%s" does not exist' % header_path)

                            with open(entry_path, 'r') as entry_point:
                                with open(header_path, 'r') as header:
                                    aux_sources[problem_id + '_submission'] = (
                                        '#include "%s"\n#define main main_%s\n' %
                                        (handler_data['header'],
                                        str(uuid.uuid4()).replace('-', ''))) + source_code
                                    aux_sources[handler_data['header']] = header.read()
                                    entry = entry_point.read()
                            # Compile as CPP11 regardless of what the submission language is
                            executor = executors[siggrader].Executor(problem_id, entry, aux_sources=aux_sources,
                                                                     writable=handler_data.get('writable', (1, 2)),
                                                                     fds=handler_data.get('fds', None))
                        else:
                            raise CompileError('no valid handler compiler exists')
                    else:
                        executor = executors[language].Executor(problem_id, source_code)
                except KeyError:
                    raise NotImplementedError('unsupported language: ' + language)
                except CompileError as e:
                    print 'Compile Error'
                    print e.args[0]
                    self.packet_manager.compile_error_packet(e.args[0])
                    return

                try:
                    # Obtain the output correctness checker, e.g. standard or float
                    checker_id = init_data.get('checker', 'standard')
                    if isinstance(checker_id, dict):
                        checker_params = checker_id.get('parameters', {})
                        checker_id = checker_id['name']
                    else:
                        checker_params = {}
                    if '.' in checker_id:
                        module_path = os.path.join(problem_root, checker_id)
                        if not os.path.exists(module_path):
                            raise IOError('checker module path "%s" does not exist' % module_path)
                        checker = load_module_from_file(module_path)
                        checker_id = checker.__name__
                    else:
                        checker = getattr(checkers, checker_id)
                except AttributeError:
                    raise NotImplementedError('error loading checker')

                print>> sys.stderr, 'Using checker %s' % checker_id

                # Use a proxy to not expose init_data to all submethods
                def check_adapter(test_input, proc_output, judge_output, point_value):
                    return checker.check(proc_output, judge_output, submission_source=source_code,
                                         judge_input=test_input, point_value=point_value,
                                         **checker_params)

                case = 1
                if hasattr(executor, 'warning') and executor.warning:
                    self.packet_manager.compile_message_packet(executor.warning)
                for result in self.run(executor, init_data, check_adapter, problem_id,
                                       time=time_limit, memory=memory_limit,
                                       short_circuit=short_circuit, source_code=original_source,
                                       interactive=('grader' in init_data)):
                    print 'Test case %s' % case
                    print '\t%f seconds (real)' % result.r_execution_time
                    print '\t%f seconds (debugged)' % result.execution_time
                    # print '\tDebugging took %.2f%% of the time' % \
                    # ((result.r_execution_time - result.execution_time) / result.r_execution_time * 100)
                    print '\t%.2f mb (%s kb)' % (result.max_memory / 1024.0, result.max_memory)

                    if result.result_flag == Result.AC:
                        print '\tAccepted'
                    else:
                        execution_verdict = []
                        for flag in ['IR', 'WA', 'RTE', 'TLE', 'MLE', 'SC', 'IE']:
                            if result.result_flag & getattr(Result, flag):
                                execution_verdict.append('\t' + flag)
                        print '\n'.join(execution_verdict)
                    case += 1
        except TerminateGrading:
            self.packet_manager.submission_terminated_packet()
            print>> sys.stderr, 'Forcefully terminating grading. Temporary files may not be deleted.'
        except:
            traceback.print_exc()
            self.packet_manager.internal_error_packet(traceback.format_exc())
        finally:
            print>> sys.stderr, '===========Done Grading: %s===========' % submission_id
            self._terminate_grading = False
            self.current_submission_thread = None
            self.current_submission = None

    def listen(self):
        """
        Attempts to connect to the handler server specified in command line.
        """
        self.packet_manager.run()

    def _resolve_open_call(self, init_data, problem_id, forward_test_cases=None):
        """
        Resolves the method for accessing testing data given the problem initialization data.
        :param init_data: 
            The problem initialization data.
        :param problem_id: 
            The problem code.
        :param forward_test_cases: 
            A list of testcases contained in init_data.
        """

        class iofile_fetcher(dict):
            def __missing__(self, key):
                return open(os.path.join(get_problem_root(problem_id), key), 'r')

        files = iofile_fetcher()

        if 'archive' in init_data:
            archive_path = os.path.join(get_problem_root(problem_id), init_data['archive'])
            if not os.path.exists(archive_path):
                raise IOError('archive file "%s" does not exist' % archive_path)
            try:
                archive = zipfile.ZipFile(archive_path, 'r')
            except zipfile.BadZipfile:
                raise IOError('Bad archive: %s' % archive_path)
            try:
                for name in archive.infolist():
                    files[name.filename] = archive.read(name)
            finally:
                archive.close()

        if 'generator' in init_data and forward_test_cases:
            generator_path = os.path.join(get_problem_root(problem_id), init_data['generator'])
            if not os.path.exists(generator_path):
                raise IOError('generator does not exist')
            try:
                with open(generator_path, "r") as generator_file:
                    generator_source = generator_file.read()
            except:
                traceback.print_exc()
                raise IOError('could not read generator source')

            _, ext = os.path.splitext(generator_path)

            def find_cpp():
                global executors
                for grader in ('CPP11', 'CPP0X', 'CPP'):
                    if grader in executors:
                        return grader
                raise CompileError("Can't grade with generator. Why did I get this submission?")

            lookup = {
                '.py': executors.get('PY2', None),
                '.py3': executors.get('PY3', None),
                '.c': executors.get('C', None),
                '.cpp': executors.get(find_cpp(), None),
                '.java': executors.get('JAVA', None),
                '.rb': executors.get('RUBY', None)
            }
            clazz = lookup.get(ext, None)
            if not clazz:
                raise IOError('could not identify generator extension')
            generator_launcher = clazz.Executor('_%s_generator' % problem_id, generator_source).launch_unsafe

            test = 0
            if self._terminate_grading:
                raise TerminateGrading()
            for test_case in forward_test_cases:
                for input_file, output_file, point_value in test_case:
                    test += 1
                    if input_file not in files or output_file not in files:
                        generator_process = generator_launcher(stdin=subprocess.PIPE,
                                                               stdout=subprocess.PIPE,
                                                               stderr=subprocess.PIPE)
                        self.current_proc = generator_process
                        generator_output, generator_error = generator_process.communicate(
                            '\n'.join((str(test), input_file, output_file, '')))
                        if self._terminate_grading:
                            raise TerminateGrading()
                        self.current_proc = None
                        if input_file not in files and generator_output and generator_output[0] != '\0':
                            files[input_file] = generator_output
                        if output_file not in files and generator_error and generator_error[0] != '\0':
                            files[output_file] = generator_error
        return files.__getitem__

    def run(self, executor, init_data, check_func, problem_id, short_circuit=False, time=2, memory=65536,
            source_code=None, interactive=False):
        """
        Executes a submission in standard (static) mode.
        :param executor:
            Executor to launch the submission program.
        :param init_data: 
            The problem initialization data.
        :param check_func: 
            Callback to check validity of the submission program output.
        :param problem_id: 
            The problem code.
        :param short_circuit:
            Whether to short-circuit batch testcases.
        :param time: 
            Time limit for submission program, in seconds.
        :param memory: 
            Memory limit for submission program, in kilobytes.
        :param interactive: 
            Boolean to indicate whether this needs a custom grader and interactor.
        :return:
            A Result instance representing the execution result of the submission program.
        """
        output_prefix_length = init_data.get('output_prefix_length', 32)
        time_adjust = init_data.get('time_adjust', 1.0)
        forward_test_cases = []
        for case in init_data['test_cases']:
            if isinstance(case, dict):
                if 'data' in case:
                    # Data is batched, with multiple subcases for each parent case
                    # If one subcase fails, the main case fails too
                    subcases = [(subcase.get('in', None), subcase.get('out', None)) for subcase in case['data']]
                    case = BatchedTestCase(subcases, int(case.get('points', 0)))
                else:
                    case = TestCase(case.get('in', None), case.get('out', None), int(case.get('points', 0)))
            else:
                # Not sure what this does, but it was in run_interactive
                case = (None, None, int(case))
            forward_test_cases.append(case)

        if interactive:
            if 'grader' not in init_data:
                raise IOError('no grader specified')
            grader_path = os.path.join(get_problem_root(problem_id), init_data['grader'])
            if not os.path.exists(grader_path):
                raise IOError('grader does not exist')

            try:
                interactive_grader = load_module_from_file(grader_path)
            except:
                traceback.print_exc()
                raise IOError('could not load grader module')
        else:
            interactive_grader = None

        topen = self._resolve_open_call(init_data, problem_id, forward_test_cases)

        self.packet_manager.begin_grading_packet()
        case_number = 1
        short_circuited = False
        try:
            for test_case in forward_test_cases:
                if isinstance(test_case, BatchedTestCase):
                    self.packet_manager.begin_batch_packet()
                for input_file, output_file, point_value in test_case:
                    if self._terminate_grading:
                        raise TerminateGrading()
                    result = Result()
                    if short_circuited:
                        # A previous subtestcase failed so we're allowed to break early
                        result.result_flag = Result.SC
                        check = CheckerResult(False, 0)
                        feedback = None
                    else:
                        _input_data = topen(input_file) if input_file else ''
                        if hasattr(_input_data, 'read'):
                            try:
                                input_data = _input_data.read()
                            finally:
                                _input_data.close()
                        else:
                            input_data = _input_data
                        if input_data:
                            input_data = input_data.replace('\r\n', '\n')  # .replace('\r', '\n')

                        _output_data = topen(output_file) if output_file else ''
                        if hasattr(_output_data, 'read'):
                            try:
                                output_data = _output_data.read()
                            finally:
                                _output_data.close()
                        else:
                            output_data = _output_data
                        if output_data:
                            output_data = output_data.replace('\r\n', '\n')  # .replace('\r', '\n')

                        # Launch a process for the current test case
                        self.current_proc = executor.launch(time=time, memory=memory, pipe_stderr=True)

                        process = self.current_proc

                        if interactive:
                            # TODO: interactive grader should really run on another thread
                            # if submission dies, interactive grader might get stuck on a process IO call,
                            # hanging the main thread
                            try:
                                result = interactive_grader.grade(case_number, process,
                                                                  case_input=input_data and cStringIO.StringIO(input_data),
                                                                  case_output=output_data and cStringIO.StringIO(output_data),
                                                                  point_value=point_value,
                                                                  source_code=source_code)
                                if isinstance(result, tuple) or isinstance(result, list):
                                    result, error = result
                                else:
                                    error = ''
                            except:
                                traceback.print_exc()
                                try:
                                    process.kill()
                                except:  # The process might've already exited
                                    pass
                                self.packet_manager.internal_error_packet(problem_id + '\n\n' + traceback.format_exc())
                                return
                            else:
                                process.wait()
                        else:
                            result.result_flag = Result.AC
                            if hasattr(process, 'safe_communicate'):
                                communicate = process.safe_communicate
                            else:
                                communicate = partial(safe_communicate, process)
                            try:
                                result.proc_output, error = communicate(input_data, outlimit=25165824, errlimit=1048576)
                            except OutputLimitExceeded as e:
                                stream, result.proc_output, error = e.args
                                print>> sys.stderr, 'OLE:', stream
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
                        if result.proc_output is None:
                            result.proc_output = ''

                        if interactive:
                            check = CheckerResult(result.result_flag == Result.AC, result.points)
                        else:
                            check = check_func(input_data, result.proc_output, output_data, point_value)
                        if not isinstance(check, CheckerResult):
                            check = CheckerResult(check, check and point_value)
                        if not check.passed:
                            result.result_flag |= Result.WA

                        if not init_data.get('swallow_ir', False) and process.returncode > 0:
                            print>> sys.stderr, 'Exited with error: %d' % process.returncode
                            result.result_flag |= Result.IR
                        if not init_data.get('swallow_rte', False) and process.returncode < 0:
                            if process.returncode is not None:
                                print>> sys.stderr, 'Killed by signal %d' % -process.returncode
                            result.result_flag |= Result.RTE  # Killed by signal
                        if not init_data.get('swallow_tle', False) and process.tle:
                            result.result_flag |= Result.TLE
                        if process.mle:
                            result.result_flag |= Result.MLE

                        if result.result_flag & ~Result.WA:
                            check.points = 0

                        feedback = (check.feedback or
                                    (process.feedback if hasattr(process, 'feedback') else
                                     getattr(executor, 'get_feedback', lambda x, y: '')(error, result)))

                    if not init_data.get('swallow_tle', False) and not (result.result_flag & Result.TLE):
                        result.execution_time *= time_adjust
                        if result.execution_time > time:
                            result.result_flag |= Result.TLE
                            check.points = 0

                    self.packet_manager.test_case_status_packet(
                        case_number, check.points, point_value, result.result_flag, result.execution_time,
                        result.max_memory,
                        result.proc_output[:output_prefix_length].decode('utf-8', 'replace'), feedback)

                    if not short_circuited and result.result_flag != Result.AC:
                        short_circuited = True
                        if point_value == 0:
                            # Pretests failed
                            short_circuit = True

                    case_number += 1
                    yield result
                if isinstance(test_case, BatchedTestCase):
                    self.packet_manager.batch_end_packet()
                if not short_circuit:
                    short_circuited = False
        except TerminateGrading:
            raise
        except IOError:
            traceback.print_exc()
            raise
        except:
            traceback.print_exc()
            self.packet_manager.grading_end_packet()
        else:
            self.packet_manager.grading_end_packet()
        finally:
            self.current_proc = None
            self._terminate_grading = False
            gc.collect()

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


def main():
    print 'Running live judge...'

    with Judge(judgeenv.server_host, judgeenv.server_port) as judge:
        try:
            judge.listen()
        finally:
            judge.murder()


if __name__ == '__main__':
    main()
