#!/usr/bin/python
import argparse
import ctypes
import inspect
import json
import os
import time
import traceback
import sys
import threading

try:
    import queue
except ImportError:
    import Queue as queue

from ptbox import sandbox  # @UnresolvedImport
from error import CompileError

import executors  # @UnresolvedImport
import checkers

import packet  # @UnresolvedImport

import zipreader  # @UnresolvedImport


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
        self.partial_output = None


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
        self.point_value = point_value
        self.io_files = list(io_files)
        self.current_case = 0

    def __iter__(self):
        return self

    def next(self):
        if self.current_case >= len(self.io_files):
            raise StopIteration
        else:
            self.current_case += 1
            return self.io_files[self.current_case - 1] + (self.point_value,)


class ThreadWithExc(threading.Thread):
    """
        A thread class that supports raising exception in the thread from
        another thread.
    """

    def throw(self, exctype):
        if not inspect.isclass(exctype):
            raise TypeError("Only types can be raised (not instances)")
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident,
                                                         ctypes.py_object(exctype))
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
            # "if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"
            ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident, 0)
            raise SystemError("PyThreadState_SetAsyncExc failed")


class TerminateGrading(Exception):
    pass


class Judge(object):
    PING_FREQUENCY = 5

    def __init__(self, host, port, debug=False, **kwargs):
        self.debug_mode = debug
        self.packet_manager = packet.PacketManager(host, port, self)
        self.current_submission = None
        self.current_proc = None
        with open(os.path.join("data", "judge", "judge.json"), "r") as init_file:
            self.env = json.load(init_file)
        supported_problems = []
        for problem in os.listdir(os.path.join("data", "problems")):
            supported_problems.append((problem, os.path.getmtime(os.path.join("data", "problems", problem))))
        self.packet_manager.supported_problems_packet(supported_problems)
        self.current_submission_thread = None

    def begin_grading(self, problem_id, language, source_code):
        print "Grading %s in %s..." % (problem_id, language)
        if self.current_submission_thread:
            # TODO: this should be an error
            self.terminate_grading()
        self.current_submission_thread = ThreadWithExc(target=self._begin_grading,
                                                       args=(problem_id, language, source_code))
        self.current_submission_thread.daemon = True
        self.current_submission_thread.start()

    def terminate_grading(self):
        if self.current_submission_thread:
            try:
                if self.current_proc:
                    self.current_proc.kill()
                self.current_submission_thread.throw(TerminateGrading)
                self.current_submission_thread.join()
            except threading.ThreadError:
                print "Successfully terminated grading."
            except:
                traceback.print_exc()
            self.current_submission_thread = None
            self.packet_manager.submission_terminated_packet()

    def _begin_grading(self, problem_id, language, source_code):
        generated_files = []
        try:
            try:
                executor = getattr(executors, language)
                generated_files = executor.generate(self.env, problem_id, source_code)
            except AttributeError:
                raise NotImplementedError("unsupported language: " + language)
            except CompileError as compile_error:
                generated_files.append(compile_error.args[1])
                print "Compile Error"
                print compile_error.args[0]
                self.packet_manager.compile_error_packet(compile_error.args[0])
                return

            with open(os.path.join("data", "problems", problem_id, "init.json"), "r") as init_file:
                init_data = json.load(init_file)
                problem_type = init_data["type"]

                try:
                    checker = getattr(checkers, problem_type)
                except AttributeError:
                    raise NotImplementedError("unsupported problem type: " + problem_type)

                # Use a proxy to not expose init_data to all submethods
                check_adapter = lambda proc_output, judge_output: checker.check(proc_output, judge_output,
                                                                                *init_data)
                forward_test_cases = []
                for case in init_data["test_cases"]:
                    if "data" in case:
                        # Data is batched, with multiple subcases for each parent case
                        # If one subcase fails, the main case fails too
                        subcases = [(subcase["in"], subcase["out"]) for subcase in case["data"]]
                        case = BatchedTestCase(subcases, case["points"])
                    else:
                        case = TestCase(case["in"], case["out"], case["points"])
                    forward_test_cases.append(case)

                case = 1
                for res in self.run_standard(executor, generated_files, forward_test_cases, check_adapter,
                                             archive=os.path.join("data", "problems", problem_id, init_data["archive"]),
                                             time=int(init_data["time"]), memory=int(init_data["memory"]),
                                             short_circuit=(init_data["short_circuit"] == "True")):
                    print "Test case %s" % case
                    print "\t%f seconds (real)" % res.r_execution_time
                    print "\t%f seconds (debugged)" % res.execution_time
                    # print "\tDebugging took %.2f%% of the time" % \
                    # ((res.r_execution_time - res.execution_time) / res.r_execution_time * 100)
                    print "\t%.2f mb (%s kb)" % (res.max_memory / 1024.0, res.max_memory)

                    if res.result_flag == Result.AC:
                        print "\tAccepted"
                    else:
                        execution_verdict = []
                        for flag in ["IR", "WA", "RTE", "TLE", "MLE", "SC", "IE"]:
                            if res.result_flag & getattr(Result, flag):
                                execution_verdict.append("\t" + flag)
                        print "\n".join(execution_verdict)
                    case += 1
        except IOError:
            print "Internal Error: Test cases do not exist"
            self.packet_manager.problem_not_exist_packet(problem_id)
        except TerminateGrading:
            print "Forcefully terminating grading. Temporary files may not be deleted."
        finally:
            for bad_file in generated_files:
                os.unlink(bad_file)
            self.current_submission_thread = None

    def listen(self):
        self.packet_manager.run()

    def run_standard(self, executor, generated_files, test_cases, checker, short_circuit=False, time=2, memory=65536,
                     *args, **kwargs):
        if "archive" in kwargs:
            archive = zipreader.ZipReader(kwargs["archive"])
            openfile = archive.files.__getitem__
        else:
            openfile = open
        self.packet_manager.begin_grading_packet()
        short_circuit_all = short_circuit
        case_number = 1
        short_circuited = False
        try:
            for test_case in test_cases:
                if type(test_case) == BatchedTestCase:
                    self.packet_manager.begin_batch_packet()
                for input_file, output_file, point_value in test_case:
                    with ProgramJudge(*args, partial_output_limit=(2147483647 if self.debug_mode else 10)) as judge:
                        result = Result()
                        if short_circuited:
                            result.result_flag = Result.SC
                            result.execution_time = 0
                            result.max_memory = 0
                            result.partial_output = ""
                        else:
                            self.current_proc = executor.launch(self.env, generated_files, time=time, memory=memory)
                            judge.run_standard(self.current_proc, result, openfile(input_file), openfile(output_file),
                                               checker)
                        self.packet_manager.test_case_status_packet(case_number,
                                                                    point_value if not short_circuited and result.result_flag == Result.AC else 0,
                                                                    point_value,
                                                                    result.result_flag,
                                                                    result.execution_time,
                                                                    result.max_memory,
                                                                    result.partial_output)
                        if not short_circuited and result.result_flag != Result.AC:
                            short_circuited = True
                        case_number += 1
                        yield result
                if type(test_case) == BatchedTestCase:
                    self.packet_manager.batch_end_packet()
                if not short_circuit_all:
                    short_circuited = False
        except:
            traceback.print_exc()
        finally:
            self.packet_manager.grading_end_packet()
        self.current_proc = None

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
        self.current_submission = "submission"
        with open(os.path.join("data", "judge", "judge.json"), "r") as init_file:
            self.env = json.load(init_file)
        self.current_submission_thread = None

    def listen(self):
        pass


class ProgramJudge(object):
    EOF = None

    def __init__(self, redirect=False, transfer=False, interact=False, partial_output_limit=10):
        self.result = None
        self.process = None
        self.write_lock = threading.Lock()
        self.write_queue = queue.Queue()
        self.stopped = False
        self.exitcode = None
        self.redirect = redirect
        self.transfer = transfer
        self.interact = interact
        self.partial_output_limit = partial_output_limit

        self.old_stdin = sys.stdin
        self.old_stdout = sys.stdout
        self.current_submission = None
        if self.redirect:
            sys.stdin = self
            sys.stdout = self

    def __del__(self):
        self.close(True)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    def alive(self, result_flag=None):
        if not self.stopped:
            self.exitcode = self.process.poll()
            if self.exitcode is not None:
                sys.stdin = self.old_stdin
                sys.stdout = self.old_stdout
                self.stopped = True
                self.result.result_flag = result_flag
                self.write_lock.acquire()
        return not self.stopped

    def close(self, force_terminate=False, result_flag=None):
        if self.result and self.alive(result_flag):
            self.result.result_flag = result_flag
            self.write_lock.acquire()
            sys.stdin = self.old_stdin
            sys.stdout = self.old_stdout
            if force_terminate or self.interact:
                self.process.terminate()
            else:
                self.exitcode = self.process.wait()
            self.stopped = True

    def read(self, *args):
        return self.process.stdout.read(*args) if self.alive() else ""

    def readline(self):
        if not self.alive():
            return ""
        line = self.process.stdout.readline().rstrip()
        while not line and self.alive():
            line = self.process.stdout.readline().rstrip()
        return line.rstrip() if line else ""

    def run_standard(self, process, result, input_file, output_file, checker):
        self.process = process
        self.result = result
        result_flag = Result.AC
        write_thread = threading.Thread(target=self.write_async, args=(self.write_lock,))
        write_thread.daemon = True
        write_thread.start()
        if self.transfer:
            self.write(sys.stdin.read())
        self.write(input_file.read())
        input_file.close()
        self.write(ProgramJudge.EOF)
        process_output = self.read()
        self.result.partial_output = process_output[:self.partial_output_limit]

        self.process.wait()
        self.result.max_memory = self.process.max_memory
        self.result.execution_time = self.process.execution_time
        self.result.r_execution_time = self.process.r_execution_time
        judge_output = output_file.read()
        output_file.close()
        if not checker(process_output, judge_output):
            result_flag |= Result.WA
        if self.process.returncode:
            result_flag |= Result.IR
        if 0:  # TODO
            result_flag |= Result.RTE
        if self.process.tle:
            result_flag |= Result.TLE
        if self.process.mle:
            result_flag |= Result.MLE
        self.close(result_flag=result_flag)

    def write(self, data):
        self.write_queue.put_nowait(data)

    def write_async(self, write_lock):
        stdin = self.process.stdin
        write_queue = self.write_queue
        try:
            while True:
                while write_lock.acquire(False) and self.alive():
                    write_lock.release()
                    try:
                        data = write_queue.get(True, 1)
                        break
                    except queue.Empty:
                        pass
                else:
                    break
                if data is ProgramJudge.EOF:
                    stdin.close()
                    break
                else:
                    data = data.replace('\r\n', '\n').replace('\r', '\n')
                    try:
                        stdin.write(data)
                    except IOError:
                        break
                    if data == '\n':
                        stdin.flush()
                        os.fsync(stdin.fileno())
        except Exception:
            traceback.print_exc()


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

    print "Running %s judge..." % (["local", "live"][args.server_host is not None])

    if args.server_host:
        with Judge(args.server_host, args.server_port, debug=args.debug) as judge:
            try:
                judge.listen()
            finally:
                judge.murder()


if __name__ == "__main__":
    main()
