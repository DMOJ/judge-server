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
from judgeerror import CompileError

import executors  # @UnresolvedImport

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


class BatchedTestCase(TestCase):
    def __init__(self, point_value, io_files):
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


def _async_raise(tid, exctype):
    '''Raises an exception in the threads with id tid'''
    if not inspect.isclass(exctype):
        raise TypeError("Only types can be raised (not instances)")
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid,
                                                     ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # "if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, 0)
        raise SystemError("PyThreadState_SetAsyncExc failed")


class ThreadWithExc(threading.Thread):
    '''A thread class that supports raising exception in the thread from
       another thread.
    '''

    def _get_my_tid(self):
        """determines this (self's) thread id

        CAREFUL : this function is executed in the context of the caller
        thread, to get the identity of the thread represented by this
        instance.
        """
        if not self.isAlive():
            raise threading.ThreadError("the thread is not active")

        # do we have it cached?
        if hasattr(self, "_thread_id"):
            return self._thread_id

        # no, look for it in the _active dict
        for tid, tobj in threading._active.items():
            if tobj is self:
                self._thread_id = tid
                return tid

        # TODO: in python 2.6, there's a simpler way to do : self.ident

        raise AssertionError("could not determine the thread's id")

    def throw(self, exctype):
        """Raises the given exception type in the context of this thread.

        If the thread is busy in a system call (time.sleep(),
        socket.accept(), ...), the exception is simply ignored.

        If you are sure that your exception should terminate the thread,
        one way to ensure that it works is:

            t = ThreadWithExc( ... )
            ...
            t.raiseExc( SomeException )
            while t.isAlive():
                time.sleep( 0.1 )
                t.raiseExc( SomeException )

        If the exception is to be caught by the thread, you need a way to
        check that your thread has caught it.

        CAREFUL : this function is executed in the context of the
        caller thread, to raise an exception in the context of the
        thread represented by this instance.
        """
        _async_raise(self._get_my_tid(), exctype)


class TerminateGrading(Exception):
    pass


class Judge(object):
    PING_FREQUENCY = 5

    def __init__(self, host, port, **kwargs):
        self.debug_mode = kwargs.get("debug", False)
        self.packet_manager = packet.PacketManager(host, port, self)
        self.current_submission = None
        with open(os.path.join("data", "judge", "judge.json"), "r") as init_file:
            self.paths = json.load(init_file)
        supported_problems = []
        for problem in os.listdir(os.path.join("data", "problems")):
            supported_problems.append((problem, os.path.getmtime(os.path.join("data", "problems", problem))))
        self.packet_manager.supported_problems_packet(supported_problems)
        self.current_submission_thread = None
        self.ping_lock = threading.Lock()
        self.ping_thread = threading.Thread(target=self.ping, args=(self.ping_lock,))
        self.ping_thread.start()

    def ping(self, ping_lock):
        total_time = 60.0 / Judge.PING_FREQUENCY
        while ping_lock.acquire(False):
            ping_lock.release()
            # TODO
            self.packet_manager.ping_packet(0)
            time_slept = 0
            while time_slept < total_time:
                if ping_lock.acquire(False):
                    ping_lock.release()
                    time.sleep(0.1)
                    time_slept += 0.1
                else:
                    break

    def begin_grading(self, problem_id, language, source_code):
        print "Grading %s in %s..." % (problem_id, language)
        if self.current_submission_thread:
            self.terminate_grading()
        self.current_submission_thread = ThreadWithExc(target=self._begin_grading,
                                                       args=(problem_id, language, source_code))
        self.current_submission_thread.daemon = True
        self.current_submission_thread.start()

    def terminate_grading(self):
        if self.current_submission_thread:
            try:
                self.current_submission_thread.throw(TerminateGrading)
                self.current_submission_thread.join()
                self.current_submission_thread = None
            except threading.ThreadError:
                print "Successfully terminated grading."
            except:
                traceback.print_exc()
            self.packet_manager.submission_terminated_packet()

    def _begin_grading(self, problem_id, language, source_code):
        try:
            try:
                generated_files = []
                try:
                    try:
                        executor = getattr(executors, language)
                        generated_files = executor.generate(self.paths, problem_id, source_code)
                    except CompileError as compile_error:
                        generated_files.append(compile_error.args[1])
                        print "Compile Error"
                        print compile_error.message
                        self.packet_manager.compile_error_packet(compile_error.message)
                        return
                except AttributeError:
                    raise NotImplementedError("%s not implemented yet!" % language)

                try:
                    with open(os.path.join("data", "problems", problem_id, "init.json"), "r") as init_file:
                        init_data = json.load(init_file)
                        problem_type = init_data["type"]
                        if problem_type == "standard":
                            run = self.run_standard
                            checker = checker_standard
                            checker_args = ()
                        elif problem_type == "floats":
                            run = self.run_standard
                            checker = checker_floats
                            checker_args = (int(init_data["precision"]),)
                        else:
                            raise Exception("not implemented yet!")
                        test_cases = init_data["test_cases"]
                        forward_test_cases = [
                            (BatchedTestCase(case["points"], ((subcase["in"], subcase["out"]) for subcase in
                                                              case["data"])) if "data" in case else
                             TestCase(case["in"], case["out"], case["points"])) for case in test_cases]
                        case = 1
                        for res in run(executor, generated_files, forward_test_cases, checker, checker_args,
                                       archive=os.path.join("data", "problems", problem_id, init_data["archive"]),
                                       time=int(init_data["time"]), memory=int(init_data["memory"]),
                                       short_circuit=(init_data["short_circuit"] == "True")):
                            print "Test case %s" % case
                            print "\t%f seconds (real)" % res.r_execution_time
                            print "\t%f seconds (debugged)" % res.execution_time
                            #print "\tDebugging took %.2f%% of the time" % \
                            #      ((res.r_execution_time - res.execution_time) / res.r_execution_time * 100)
                            print "\t%.2f mb (%s kb)" % (res.max_memory / 1024.0, res.max_memory)
                            execution_verdict = []
                            if res.result_flag & Result.IR:
                                execution_verdict.append("\tInvalid Return")
                            if res.result_flag & Result.WA:
                                execution_verdict.append("\tWrong Answer")
                            if res.result_flag & Result.RTE:
                                execution_verdict.append("\tRuntime Error")
                            if res.result_flag & Result.TLE:
                                execution_verdict.append("\tTime Limit Exceeded")
                            if res.result_flag & Result.MLE:
                                execution_verdict.append("\tMemory Limit Exceeded")
                            if res.result_flag & Result.SC:
                                execution_verdict.append("\tShort Circuited")
                            if res.result_flag & Result.IE:
                                execution_verdict.append("\tInternal Error")
                            if res.result_flag == Result.AC:
                                print "\tAccepted"
                            else:
                                print "\n".join(execution_verdict)
                            case += 1
                except IOError:
                    print "Internal Error: Test cases do not exist"
                    self.packet_manager.problem_not_exist_packet(problem_id)
            finally:
                for bad_file in generated_files:
                    os.unlink(bad_file)
        except TerminateGrading:
            print "Forcefully terminating grading. Temporary files may not be deleted."
        finally:
            self.current_submission_thread = None

    def listen(self):
        self.packet_manager.run()

    def run_standard(self, executor, generated_files, test_cases, checker, checker_args, *args, **kwargs):
        if "archive" in kwargs:
            archive = zipreader.ZipReader(kwargs["archive"])
            openfile = archive.files.__getitem__
        else:
            openfile = open
        self.packet_manager.begin_grading_packet()
        short_circuit_all = kwargs.get("short_circuit", False)
        case_number = 1
        short_circuited = False
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
                        process = executor.launch(self.paths, sandbox.execute, generated_files,
                                                  time=kwargs.get("time", 2), memory=kwargs.get("memory", 65536))
                        judge.run_standard(process, result, openfile(input_file), openfile(output_file),
                                           checker, checker_args)
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
        self.packet_manager.grading_end_packet()

    # TODO: cleanup packet manager
    def __del__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.ping_lock.acquire()

    def murder(self):
        self.terminate_grading()


class LocalJudge(Judge):
    def __init__(self, **kwargs):
        self.debug_mode = kwargs.get("debug", False)

        class LocalPacketManager(object):
            def __getattr__(self, *args, **kwargs):
                return lambda *args, **kwargs: None

        self.packet_manager = LocalPacketManager()
        self.current_submission = "submission"
        with open(os.path.join("data", "judge", "judge.json"), "r") as init_file:
            self.paths = json.load(init_file)
        self.current_submission_thread = None
        self.ping_lock = threading.Lock()
        self.ping_thread = threading.Thread(target=self.ping, args=(self.ping_lock,))
        self.ping_thread.start()

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

    def run_standard(self, process, result, input_file, output_file, checker, checker_args):
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
        if not checker(process_output, judge_output, *checker_args):
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


def checker_standard(process_output, judge_output):
    for process_line, judge_line in zip(process_output.split('\n'), judge_output.split('\n')):
        process_line = process_line.rstrip()
        judge_line = judge_line.rstrip()
        if process_line != judge_line:
            return False
    return True


def checker_floats(process_output, judge_output, precision):
    epsilon = 10 ** -precision
    for process_line, judge_line in zip(process_output.split('\n'), judge_output.split('\n')):
        try:
            process_floats = map(float, process_line.split())
            judge_floats = map(float, judge_line.split())
        except TerminateGrading:
            raise
        except:
            return False
        for process_float, judge_float in zip(process_floats, judge_floats):
            if abs(process_float - judge_float) > epsilon:
                return False
    return True


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

    cpp_source = r'''
#include <iostream>
#include <cstdio>

using namespace std;

int main()
{
    int N, a, b;
    scanf("%d",  &N);
    for(int i=0; i<N; i++)
    {
        scanf("%d%d", &a, &b);
        printf("%d\n", a+b);
    }

    return 0;
}
'''

    cpp11_source = r'''
#include <iostream>
#include <cstdio>
#include <unordered_set>

using namespace std;

int main()
{
    int N, a, b;
    scanf("%d",  &N);
    for(int i=0; i<N; i++)
    {
        scanf("%d%d", &a, &b);
        printf("%d\n", a+b);
    }

    return 0;
}
'''

    java_source = '''
import java.util.Scanner;
import java.io.*;

public class aplusb
{
    public static void main(String args[]) throws IOException
    {
        //File f = new File("a.b");
        //f.createNewFile();
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        for(int i = 0; i != n; i++) {
            System.out.println(sc.nextInt() + sc.nextInt());
        }
        sc.close();
    }
}
'''

    rb_source = r'''
n = Integer(gets)
n.times {
    l = gets.split
    puts Integer(l[0]) + Integer(l[1])
}
'''

    py2_source = r'''
n = input()
for i in xrange(n):
    print sum(map(int, raw_input().split()))
'''

    py3_source = r'''
for i in range(int(input())):
    print(sum(map(int, input().split())))
'''

    geom_py2_source = r'''
import math
def cp(x1, y1, x2, y2):
    return x1*y2-y1*x2
def area(x, y, z):
    return abs(cp(x[0]-y[0], x[1]-y[1], x[0]-z[0], x[1]-z[1]))/2.0
def perim(x, y, z):
    return math.hypot(x[0]-y[0], x[1]-y[1])+math.hypot(x[0]-z[0], x[1]-z[1])+math.hypot(y[0]-z[0], y[1]-z[1])
for i in xrange(input()):
    x1, y1, x2, y2, x3, y3=map(int, raw_input().split())
    X=x1, y1
    Y=x2, y2
    Z=x3, y3
    print "%.2f %.2f"%(area(X, Y, Z), perim(X, Y, Z))
'''

    #import yappi

    #yappi.start()

    if args.server_host:
        judge = Judge(args.server_host, args.server_port, debug=args.debug)
        try:
            judge.listen()
        finally:
            judge.murder()
    else:
        with LocalJudge(debug=args.debug) as judge:
            try:
                #judge.begin_grading("aplusb", "CPP", cpp_source)
                #judge.begin_grading("aplusb", "RUBY", rb_source)

                judge.begin_grading("aplusb", "CPP11", cpp11_source)
                judge.current_submission_thread.join()
                judge.begin_grading("aplusb", "JAVA", java_source)
                judge.current_submission_thread.join()
                judge.begin_grading("helloworld", "PY3", 'print("Hello, World!")')
                judge.current_submission_thread.join()
                judge.begin_grading("geometry1", "PY2", geom_py2_source)
                judge.current_submission_thread.join()
                judge.begin_grading("aplusb", "PY2", py2_source)
                judge.current_submission_thread.join()
                judge.begin_grading("aplusb", "PY3", py3_source)
                judge.current_submission_thread.join()
                # time.sleep(0.1)
                # #judge.terminate_grading()
                # while judge.current_submission_thread is not None:
                #     #print "submission alive?", judge.current_submission_thread.isAlive()
                #     time.sleep(0.1)
            except Exception:
                traceback.print_exc()
        print "Done"
        # yappi.get_func_stats().print_all()


if __name__ == "__main__":
    main()
