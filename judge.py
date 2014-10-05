#!/usr/bin/python
import argparse
import copy
import gc
import json
import os
import traceback
import threading
import zipfile
import cStringIO
import sys
import subprocess

from error import CompileError
from judgeenv import env

from executors import executors
import checkers
import packet


class Result(object):
    AC = 0
    WA = 1 << 0
    RTE = 1 << 1
    TLE = 1 << 2
    MLE = 1 << 3
    IR = 1 << 4
    SC = 1 << 5
    IE = 1 << 30

    def __init__(self):
        self.result_flag = 0
        self.execution_time = 0
        self.r_execution_time = 0
        self.max_memory = 0
        self.proc_output = None
        self.points = 0


class TestCase(object):
    def __init__(self, input_file, output_file, point_value):
        self.input_file = input_file
        self.output_file = output_file
        self.point_value = point_value
        self.complete = False

    def __iter__(self):
        return self

    def next(self):
        if self.complete:
            raise StopIteration
        self.complete = True
        return self.input_file, self.output_file, self.point_value


class BatchedTestCase(object):
    def __init__(self, io_files, point_value):
        self.io_files = list(io_files)
        self.point_value = point_value
        self._current_case = 0

    def __iter__(self):
        return self

    def next(self):
        if self._current_case >= len(self.io_files):
            raise StopIteration
        else:
            self._current_case += 1
            return self.io_files[self._current_case - 1] + (self.point_value,)


class TerminateGrading(Exception):
    pass


class Judge(object):
    def __init__(self, host, port, **kwargs):
        self.packet_manager = packet.PacketManager(host, port, self)
        self.current_submission = None
        self.current_proc = None
        supported_problems = []
        for problem in os.listdir(os.path.join('data', 'problems')):
            supported_problems.append((problem, os.path.getmtime(os.path.join('data', 'problems', problem))))
        self.packet_manager.handshake(supported_problems, env['id'], env['key'])
        self.current_submission_thread = None
        self._terminate_grading = False

    def begin_grading(self, id, problem_id, language, source_code, time, mem, sc, grader, args):
        print 'Grading %s in %s...' % (problem_id, language)
        try:
            self.current_submission_thread.join()
        except AttributeError:
            pass
        # if self.current_submission_thread:
        # print 'TODO: this should be an error'
        # self.terminate_grading()
        self.current_submission = id
        self.current_submission_thread = threading.Thread(target=self._begin_grading,
                                                          args=(problem_id, language, source_code,
                                                                time, mem, sc, grader, args))
        self.current_submission_thread.daemon = True
        self.current_submission_thread.start()

    def terminate_grading(self):
        if self.current_submission_thread:
            self._terminate_grading = True
            if self.current_proc:
                self.current_proc.kill()
            self.current_submission_thread.join()

    def _begin_grading(self, problem_id, language, source_code, time_limit, memory_limit, short_circuit, grader_id,
                       grader_args):
        submission_id = self.current_submission
        print>> sys.stderr, '===========Started Grading: %s===========' % submission_id
        try:
            if isinstance(source_code, unicode):
                source_code = source_code.encode('utf-8')
            try:
                # Launch an executor for the given language
                # The executor is responsible for writing source files and compiling (if applicable)
                executor = executors[language].Executor(problem_id, source_code)
            except KeyError:
                raise NotImplementedError('unsupported language: ' + language)
            except CompileError as e:
                print 'Compile Error'
                print e.args[0]
                self.packet_manager.compile_error_packet(e.args[0])
                return

            with open(os.path.join('data', 'problems', problem_id, 'init.json'), 'r') as init_file:
                init_data = json.load(init_file)

                try:
                    # Obtain the output correctness checker, e.g. standard or float
                    checker = getattr(checkers, grader_id)
                except AttributeError:
                    raise NotImplementedError('unsupported problem type: ' + grader_id)

                # Use a proxy to not expose init_data to all submethods
                check_adapter = lambda proc_output, judge_output: checker.check(proc_output, judge_output, grader_args)

                run_call = [self.run_standard, self.run_interactive]['grader' in init_data]

                case = 1
                for result in run_call(executor.launch, init_data, check_adapter, problem_id,
                                       time=time_limit, memory=memory_limit,
                                       short_circuit=short_circuit):
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
        except IOError:
            print 'Internal Error: test cases do not exist'
            traceback.print_exc()
            self.packet_manager.problem_not_exist_packet(problem_id)
        except TerminateGrading:
            print 'Forcefully terminating grading. Temporary files may not be deleted.'
        finally:
            print>> sys.stderr, '===========Done Grading: %s===========' % submission_id
            self.current_submission_thread = None
            self.current_submission = None

    def listen(self):
        self.packet_manager.run()

    def run_interactive(self, executor_func, init_data, check_adapter, problem_id, short_circuit=False, time=2, memory=65536):
        forward_test_cases = []
        for case in init_data['test_cases']:
            case = TestCase(case.get('in', None), case.get('out', None), case['points'])
            forward_test_cases.append(case)

        if 'grader' not in init_data:
            raise IOError('no grader specified')
        grader_path = os.path.join('data', 'problems', problem_id, init_data['grader'])
        if not os.path.exists(grader_path):
            raise IOError('grader does not exist')

        interactive_grader = [None]

        def set_entry_point(func):
            interactive_grader[0] = func
            print "Hooked interactive grader:", func

        try:
            with open(grader_path, 'r') as f:
                code = compile(f.read(), grader_path, 'exec')
        except:
            raise IOError('could not open grader file')

        try:
            exec code in {'__judge__': self,
                            'set_entry_point': set_entry_point,
                            'Result': Result}
        except:
            traceback.print_exc()
            self.packet_manager.submission_terminated_packet()
            # TODO: the rest of this method might normally `yield` results, so if we ever IE its probably
            # TODO: because I was on a bus while writing this and had no time to find out how this method is supposed
            # TODO: to behave
            return

        interactive_grader = interactive_grader[0]

        if not interactive_grader:
            raise IOError('no grader specified')

        if 'archive' in init_data:
            files = {}
            archive = zipfile.ZipFile(os.path.join('data', 'problems', problem_id,
                                                   init_data['archive']), 'r')
            try:
                for name in archive.infolist():
                    files[name.filename] = cStringIO.StringIO(archive.read(name))
            finally:
                archive.close()
            topen = lambda x: files[x].open
        else:
            topen = open

        self.packet_manager.begin_grading_packet()
        case_number = 1
        short_circuited = False
        try:
            for test_case in forward_test_cases:
                for input_file, output_file, point_value in test_case:
                    if self._terminate_grading:
                        raise TerminateGrading()

                    _input = topen(input_file) if input_file else None
                    _output = topen(output_file) if output_file else None
                    # Launch a process for the current test case
                    process = executor_func(time=time, memory=memory)
                    self.current_proc = process
                    # TODO: interactive grader should really run on another thread
                    # if submission dies, interactive grader might get stuck on a process IO call,
                    # hanging the main thread
                    try:
                        result = interactive_grader(case_number, self.current_proc, case_input=_input,
                                                    case_output=_output, point_value=point_value)
                    except:
                        traceback.print_exc()
                        try:
                            process.kill()
                        except:  # The process might've already exited
                            pass
                        self.packet_manager.problem_not_exist_packet(problem_id)
                        return
                    else:
                        process.wait()
                    result.max_memory = process.max_memory
                    result.execution_time = process.execution_time
                    result.r_execution_time = process.r_execution_time

                    if process.returncode > 0:
                        result.result_flag |= Result.IR
                    if process.returncode < 0:
                        #print>> sys.stderr, 'Killed by signal %d' % -process.returncode
                        result.result_flag |= Result.RTE  # Killed by signal
                    if process.tle:
                        result.result_flag |= Result.TLE
                    if process.mle:
                        result.result_flag |= Result.MLE

                    # Must check here because we might be interrupted mid-execution
                    # If we don't bail out, we get an IR.
                    if self._terminate_grading:
                        raise TerminateGrading()
                    self.packet_manager.test_case_status_packet(case_number,
                                                                result.points,
                                                                point_value,
                                                                result.result_flag,
                                                                result.execution_time,
                                                                result.max_memory,
                                                                # TODO: make limit configurable
                                                                #result.proc_output[:10
                                                                '')

                    if not short_circuited and result.result_flag != Result.AC:
                        short_circuited = True
                    case_number += 1
                    yield result
            self.packet_manager.grading_end_packet()
        except TerminateGrading:
            self.packet_manager.submission_terminated_packet()
            raise
        except:
            traceback.print_exc()
            self.packet_manager.problem_not_exist_packet(problem_id)
        finally:
            self.current_proc = None
            self._terminate_grading = False
            gc.collect()

    def run_standard(self, executor_func, init_data, check_func, problem_id, short_circuit=False, time=2, memory=65536):
        forward_test_cases = []
        for case in init_data['test_cases']:
            if 'data' in case:
                # Data is batched, with multiple subcases for each parent case
                # If one subcase fails, the main case fails too
                subcases = [(subcase['in'], subcase['out']) for subcase in case['data']]
                case = BatchedTestCase(subcases, case['points'])
            else:
                case = TestCase(case['in'], case['out'], case['points'])
            forward_test_cases.append(case)

        if 'archive' in init_data:
            files = {}
            archive = zipfile.ZipFile(os.path.join('data', 'problems', problem_id,
                                                   init_data['archive']), 'r')
            try:
                for name in archive.infolist():
                    files[name.filename] = cStringIO.StringIO(archive.read(name))
            finally:
                archive.close()
            topen = files.__getitem__
        elif 'generator' in init_data:
            files = {}
            generator_path = os.path.join('data', 'problems', problem_id, init_data['generator'])
            if not os.path.exists(generator_path):
                raise IOError('grader does not exist')
            try:
                with open(generator_path, "r") as generator_file:
                    generator_source = generator_file.read()
            except:
                print 'Internal Error: failed reading generator'
                traceback.print_exc()
                raise
            try:
                generator_extension = init_data['generator'][init_data['generator'].rfind('.') + 1:]
            except:
                print 'Internal Error: could not identify generator extension'
                traceback.print_exc()
                raise
            generator_launcher = executors['AUTO'].Executor('%s-generator' % problem_id, generator_source, generator_extension).launch_unsafe
            test = 0
            copied_forward_test_cases = copy.deepcopy(forward_test_cases)
            for test_case in copied_forward_test_cases:
                for input_file, output_file, point_value in test_case:
                    test += 1
                    generator_process = generator_launcher(stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    generator_process.stdin.write('\n'.join((str(test), input_file, output_file, '')))
                    generator_process.stdin.flush()
                    files[input_file] = generator_process.stdout
                    files[output_file] = generator_process.stderr
            topen = files.__getitem__
        else:
            topen = open
        self.packet_manager.begin_grading_packet()
        short_circuit_all = short_circuit
        case_number = 1
        short_circuited = False
        try:
            for test_case in forward_test_cases:
                if type(test_case) == BatchedTestCase:
                    self.packet_manager.begin_batch_packet()
                for input_file, output_file, point_value in test_case:
                    if self._terminate_grading:
                        raise TerminateGrading()
                    with TestCaseJudge() as judge:
                        if short_circuited:
                            # A previous subtestcase failed so we're allowed to break early
                            result = Result()
                            result.result_flag = Result.SC
                            result.execution_time = 0
                            result.max_memory = 0
                            result.proc_output = ''
                            continue

                        # Launch a process for the current test case
                        self.current_proc = executor_func(time=time, memory=memory)
                        result = judge.run_standard(self.current_proc, topen(input_file), topen(output_file),
                                                    check_func)
                        # Must check here because we might be interrupted mid-execution
                        # If we don't bail out, we get an IR.
                        if self._terminate_grading:
                            raise TerminateGrading()
                        self.packet_manager.test_case_status_packet(case_number,
                                                                    point_value if not short_circuited and result.result_flag == Result.AC else 0,
                                                                    point_value,
                                                                    result.result_flag,
                                                                    result.execution_time,
                                                                    result.max_memory,
                                                                    # TODO: make limit configurable
                                                                    result.proc_output[:10].decode('utf-8', 'replace'))

                        if not short_circuited and result.result_flag != Result.AC:
                            short_circuited = True
                        case_number += 1
                        yield result
                if type(test_case) == BatchedTestCase:
                    self.packet_manager.batch_end_packet()
                if not short_circuit_all:
                    short_circuited = False
        except TerminateGrading:
            self.packet_manager.submission_terminated_packet()
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
        del self.packet_manager

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        pass

    def murder(self):
        self.terminate_grading()


class LocalJudge(Judge):
    def __init__(self, debug=False, **kwargs):
        self.debug_mode = debug

        class LocalPacketManager(object):
            def __getattr__(self, *args, **kwargs):
                return lambda *args, **kwargs: None

        self.packet_manager = LocalPacketManager()
        self.current_submission = 'submission'
        self.current_submission_thread = None
        self._terminate_grading = False
        self.current_proc = None

    def listen(self):
        pass


class TestCaseJudge(object):
    EOF = None

    def __init__(self):
        self.result = None
        self.process = None
        self.stopped = False
        self.exitcode = None

    def __del__(self):
        self.close(True)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    def alive(self):
        if not self.stopped:
            self.exitcode = self.process.poll()
            self.stopped = self.exitcode is not None
        return not self.stopped

    def close(self, force_terminate=False):
        if self.result and self.alive():
            if force_terminate:
                self.process.kill()
            else:
                self.exitcode = self.process.wait()
            self.stopped = True

    def run_standard(self, process, input_file, output_file, checker):
        self.process = process
        self.result = Result()
        result_flag = Result.AC
        input_data = input_file.read().replace('\r\n', '\n')  # .replace('\r', '\n')

        self.result.proc_output, error = process.communicate(input_data)

        self.result.max_memory = self.process.max_memory
        self.result.execution_time = self.process.execution_time
        self.result.r_execution_time = self.process.r_execution_time
        judge_output = output_file.read()
        output_file.close()
        if not checker(self.result.proc_output, judge_output):
            result_flag |= Result.WA
        if self.process.returncode > 0:
            result_flag |= Result.IR
        if self.process.returncode < 0:
            print>> sys.stderr, 'Killed by signal %d' % -self.process.returncode
            result_flag |= Result.RTE  # Killed by signal
        if self.process.tle:
            result_flag |= Result.TLE
        if self.process.mle:
            result_flag |= Result.MLE
        # self.close()
        self.result.result_flag = result_flag
        return self.result


def main():
    parser = argparse.ArgumentParser(description='''
        Spawns a judge for a submission server.
    ''')
    parser.add_argument('server_host', nargs='?', default=None,
                        help='host to listen for the server')
    parser.add_argument('-p', '--server-port', type=int, default=9999,
                        help='port to listen for the server')
    parser.add_argument('-d', '--debug', type=bool, default=False,
                        help='enable debug mode (full output)')
    args = parser.parse_args()

    print 'Running %s judge...' % (['local', 'live'][args.server_host is not None])

    if args.server_host:
        with Judge(args.server_host, args.server_port, debug=args.debug) as judge:
            try:
                judge.listen()
            finally:
                judge.murder()
    else:
        with LocalJudge() as judge:
            try:
                # judge.begin_grading('helloworld', 'PY2', 'print "Hello, World!"', 1, 16384, 0, 'standard', {})
                # judge.current_submission_thread.join()
                judge.begin_grading('helloworld', 'RUBY', "puts 'Hello, World!'", 1, 16384, 0, 'standard', {})
                judge.current_submission_thread.join()
                # judge.begin_grading('aplusb', 'PY2', 'for i in xrange(input()): print sum(map(int, raw_input().split()))')
                # judge.current_submission_thread.join()
                judge.begin_grading('aplusb', 'PY3',
                                    'for i in range(int(input())): print(sum(map(int, input().split())))',
                                    5, 16384, 0, 'standard', {})
                judge.current_submission_thread.join()
            except KeyboardInterrupt:
                judge.terminate_grading()


if __name__ == '__main__':
    main()
