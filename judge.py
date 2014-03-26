#!/usr/bin/python
import argparse
import json
import os
import time
import traceback
import subprocess
import sys
import threading

try:
    import queue
except ImportError:
    import Queue as queue

import execute  # @UnresolvedImport

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
        self.ping_lock = threading.Lock()
        self.ping_thread = threading.Thread(target=self.ping, args=(self.ping_lock,))
        self.ping_thread.start()

    def ping(self, ping_lock):
        while ping_lock.acquire(False):
            ping_lock.release()
            # TODO
            self.packet_manager.ping_packet(0)
            time.sleep(1.0 / Judge.PING_FREQUENCY)

    def begin_grading(self, problem_id, language, source_code):
        bad_files = []
        try:
            try:
                executor = getattr(executors, language)
                bad_files, arguments = executor.generate(self.paths, problem_id, source_code)
            except executors.CompileError, compile_error:
                bad_files.append(compile_error.args[1])
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
                    (BatchedTestCase(case["points"], ((subcase["in"], subcase["out"]) for subcase in case["data"])) if "data" in case else
                     TestCase(case["in"], case["out"], case["points"])) for case in test_cases]
                case = 1
                for res in run(arguments, forward_test_cases, checker, checker_args,
                               archive=os.path.join("data", "problems", problem_id, init_data["archive"]),
                               time=int(init_data["time"]), memory=int(init_data["memory"]),
                               short_circuit=(init_data["short_circuit"] == "True")):
                    print "Test case %s" % case
                    print "\t%f seconds" % res.execution_time
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
            for bad_file in bad_files:
                os.unlink(bad_file)

    def listen(self):
        self.packet_manager.run()

    def run_standard(self, arguments, test_cases, checker, checker_args, *args, **kwargs):
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
                with ProgramJudge(arguments, *args,
                                  partial_output_limit=(2147483647 if self.debug_mode else 10)) as judge:
                    result = Result()
                    if short_circuited:
                        result.result_flag = Result.SC
                        result.execution_time = 0
                        result.max_memory = 0
                        result.partial_output = ""
                    else:
                        judge.run_standard(result, openfile(input_file), openfile(output_file),
                                           kwargs.get("time", 2), kwargs.get("memory", 65536),
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
        self.ping_lock = threading.Lock()
        self.ping_thread = threading.Thread(target=self.ping, args=(self.ping_lock,))
        self.ping_thread.start()

    def listen(self):
        pass


class ProgramJudge(object):
    EOF = None

    def __init__(self, process_name, redirect=False, transfer=False, interact=False, partial_output_limit=10):
        self.result = None
        self.process = None
        self.write_lock = threading.Lock()
        self.write_queue = queue.Queue()
        self.stopped = False
        self.exitcode = None
        self.process_name = process_name
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

    def run_standard(self, result, input_file, output_file, time_limit, memory_limit, checker, checker_args):
        self.result = result
        result_flag = Result.AC
        try:
            self.process = execute.execute(self.process_name, time_limit, memory_limit)
        except:
            traceback.print_exc()
        write_thread = threading.Thread(target=self.write_async, args=(self.write_lock,))
        write_thread.daemon = True
        write_thread.start()
        if self.transfer:
            self.write(sys.stdin.read())
        self.write(input_file.read())
        self.write(ProgramJudge.EOF)
        process_output = self.read()
        self.result.partial_output = process_output[:self.partial_output_limit]
        #print process_output
        self.result.max_memory = self.process.get_max_memory()
        self.result.execution_time = self.process.get_execution_time()
        judge_output = output_file.read()
        if not checker(process_output, judge_output, *checker_args):
            result_flag |= Result.WA
        self.process.poll()
        if self.process.returncode:
            result_flag |= Result.IR
        if self.process.get_rte():
            result_flag |= Result.RTE
        if self.process.get_tle():
            result_flag |= Result.TLE
        if self.process.get_mle():
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

    py2_source = r'''
n = input()
for i in xrange(n):
    print sum(map(int, raw_input().split()))
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

    if args.server_host:
        judge = Judge(args.server_host, args.server_port, debug=args.debug)
        judge.listen()
    else:
        with LocalJudge(debug=args.debug) as judge:
            try:
                #judge.begin_grading("aplusb", "CPP", cpp_source)
                #judge.begin_grading("aplusb", "CPP11", cpp11_source)
                #judge.begin_grading("aplusb", "JAVA", java_source)
                #judge.begin_grading("aplusb", "PY2", py2_source)
                judge.begin_grading("geometry1", "PY2", geom_py2_source)
                #judge.begin_grading("aplusb_batch", "PY2", py2_source)
            except Exception:
                traceback.print_exc()
        print "Done"


if __name__ == "__main__":
    main()
