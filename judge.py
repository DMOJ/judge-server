#!/usr/bin/python
import argparse
import copy
from functools import partial
import gc
import json
import os
import traceback
import threading
import zipfile
import cStringIO
import sys
import subprocess
from communicate import safe_communicate, OutputLimitExceeded

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print>> sys.stderr, 'No Watchdog!'
    Observer = None

    class FileSystemEventHandler(object):
        pass

from error import CompileError
from judgeenv import env
from communicate import safe_communicate, OutputLimitExceeded

from executors import executors
import checkers
import packet
import imp


class Result(object):
    AC = 0
    WA = 1 << 0
    RTE = 1 << 1
    TLE = 1 << 2
    MLE = 1 << 3
    IR = 1 << 4
    SC = 1 << 5
    OLE = 1 << 6
    IE = 1 << 30

    def __init__(self):
        self.result_flag = 0
        self.execution_time = 0
        self.r_execution_time = 0
        self.max_memory = 0
        self.proc_output = ''
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

    def begin_grading(self, id, problem_id, language, source_code, time, mem, sc):
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
                                                                time, mem, sc))
        self.current_submission_thread.daemon = True
        self.current_submission_thread.start()

    def terminate_grading(self):
        if self.current_submission_thread:
            self._terminate_grading = True
            if self.current_proc:
                self.current_proc.kill()
            self.current_submission_thread.join()

    def _begin_grading(self, problem_id, language, source_code, time_limit, memory_limit, short_circuit):
        submission_id = self.current_submission
        print>> sys.stderr, '===========Started Grading: %s===========' % submission_id
        try:
            with open(os.path.join('data', 'problems', problem_id, 'init.json'), 'r') as init_file:
                init_data = json.load(init_file)

                if isinstance(source_code, unicode):
                    source_code = source_code.encode('utf-8')
                try:
                    # Launch an executor for the given language
                    # The executor is responsible for writing source files and compiling (if applicable)
                    if 'handler' in init_data and language in ['C', 'CPP', 'CPP11']:
                        aux_sources = {}
                        handler_data = init_data['handler']
                        with open(os.path.join('data', 'problems', problem_id, handler_data['entry']), 'r') as i:
                            with open(os.path.join('data', 'problems', problem_id, handler_data['header']), 'r') as j:
                                aux_sources[problem_id + "-submission"] = ('#include "%s"\n#define main user_main\n' %
                                                                           handler_data['header']) + source_code
                                aux_sources[handler_data['header']] = j.read()
                                source_code = i.read()

                        executor = executors[language].Executor(problem_id, source_code, aux_sources=aux_sources)
                    else:
                        aux_sources = {}
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
                    grader_id = init_data.get('checker', 'standard')
                    if isinstance(grader_id, dict):
                        grader_id = grader_id['name']
                        grader_args = grader_id['parameters']
                    else:
                        grader_args = {}
                    if '.' in grader_id:
                        mod, ext = os.path.splitext(grader_id)
                        checker = imp.load_module(mod,
                                                  open(os.path.join('data', 'problems', problem_id, grader_id), 'r'),
                                                  grader_id, ('.py', 'U', 1))
                        sys.modules.pop(mod)
                        grader_id = mod
                    else:
                        checker = getattr(checkers, grader_id)
                except AttributeError:
                    raise NotImplementedError('error loading checker')


                # Use a proxy to not expose init_data to all submethods

                check_adapter = lambda test_input, proc_output, judge_output: checker.check(proc_output,
                                                                                judge_output,
                                                                                submission_source=source_code,
                                                                                test_case_data=test_input,
                                                                                **grader_args)

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

    def _resolve_open_call(self, init_data, problem_id, forward_test_cases=None):
        if 'archive' in init_data:
            files = {}
            archive = zipfile.ZipFile(os.path.join('data', 'problems', problem_id,
                                                   init_data['archive']), 'r')
            try:
                for name in archive.infolist():
                    files[name.filename] = cStringIO.StringIO(archive.read(name))
            finally:
                archive.close()
            return files.__getitem__
        elif 'generator' in init_data and forward_test_cases:
            files = {}
            generator_path = os.path.join('data', 'problems', problem_id, init_data['generator'])
            if not os.path.exists(generator_path):
                raise IOError('generator does not exist')
            try:
                with open(generator_path, "r") as generator_file:
                    generator_source = generator_file.read()
            except:
                traceback.print_exc()
                raise IOError('could not read generator source')

            _, ext = os.path.splitext(init_data['generator'])
            lookup = {
                '.py': executors.get('PY2', None),
                '.py3': executors.get('PY3', None),
                '.c': executors.get('C', None),
                '.cpp': executors.get('CPP11', None),
                '.java': executors.get('JAVA', None),
                '.rb': executors.get('RUBY', None)
            }
            clazz = lookup.get(ext, None)
            if not clazz:
                raise IOError('could not identify generator extension')
            generator_launcher = clazz.Executor('%s-generator' % problem_id, generator_source).launch_unsafe

            test = 0
            copied_forward_test_cases = copy.deepcopy(forward_test_cases)
            for test_case in copied_forward_test_cases:
                for input_file, output_file, point_value in test_case:
                    test += 1
                    generator_process = generator_launcher(stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                                           stderr=subprocess.PIPE)
                    generator_output, generator_error = generator_process.communicate(
                        '\n'.join((str(test), input_file, output_file, '')))
                    files[input_file] = cStringIO.StringIO(generator_output)
                    files[output_file] = cStringIO.StringIO(generator_error)
            return files.__getitem__
        else:
            return lambda f: open(os.path.join('data', 'problems', problem_id, f), 'r')

    def run_interactive(self, executor_func, init_data, check_adapter, problem_id, short_circuit=False, time=2,
                        memory=65536):
        forward_test_cases = []
        for case in init_data['test_cases']:
            if isinstance(case, dict):
                case = TestCase(case.get('in', None), case.get('out', None), case['points'])
            else:
                case = (None, None, int(case))
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

        topen = self._resolve_open_call(init_data, problem_id)

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
                        print>> sys.stderr, 'Killed by signal %d' % -process.returncode
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
                                                                # result.proc_output[:10
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

        topen = self._resolve_open_call(init_data, problem_id, forward_test_cases)

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
                    result = Result()
                    if short_circuited:
                        # A previous subtestcase failed so we're allowed to break early
                        result.result_flag = Result.SC
                    else:
                        # Launch a process for the current test case
                        self.current_proc = executor_func(time=time, memory=memory)

                        process = self.current_proc
                        result = Result()
                        result.result_flag = Result.AC
                        input_data = topen(input_file).read().replace('\r\n', '\n')  # .replace('\r', '\n')

                        if hasattr(process, 'safe_communicate'):
                            communicate = process.safe_communicate
                        else:
                            communicate = partial(safe_communicate, process)
                        try:
                            result.proc_output, error = communicate(input_data)
                        except OutputLimitExceeded as e:
                            stream, result.proc_output, error = e.args
                            print>> sys.stderr, 'OLE:', stream
                            result.result_flag |= Result.OLE
                            process.kill()
                            process.wait()

                        result.max_memory = process.max_memory
                        result.execution_time = process.execution_time
                        result.r_execution_time = process.r_execution_time
                        if not check_func(input_data, result.proc_output, topen(output_file).read()):
                            result.result_flag |= Result.WA
                        if process.returncode > 0:
                            result.result_flag |= Result.IR
                        if process.returncode < 0:
                            if process.returncode is not None:
                                print>>sys.stderr, 'Killed by signal %d' % -process.returncode
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
                                                                point_value if result.result_flag == Result.AC else 0,
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


def main():
    parser = argparse.ArgumentParser(description='''
        Spawns a judge for a submission server.
    ''')
    parser.add_argument('server_host', nargs='?',
                        help='host to listen for the server')
    parser.add_argument('-p', '--server-port', type=int, default=9999,
                        help='port to listen for the server')
    args = parser.parse_args()

    print 'Running live judge...'

    with Judge(args.server_host, args.server_port) as judge:
        try:
            judge.listen()
        finally:
            judge.murder()


if __name__ == '__main__':
    main()
