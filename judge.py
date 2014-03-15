#!/usr/bin/python
import os
import Queue
import subprocess
import sys
import thread
import threading

import execute
import packet


class Result(object):
    AC = 0x0
    WA = 0x1
    RTE = 0x2
    TLE = 0x4

    def __init__(self, parent):
        self.parent = parent
        self.result_flag = 0
        self.elapsed_time = 0
        self.max_memory = 0
        self.partial_output = ""

    def give_partial_output(self, partial_output):
        self.partial_output = partial_output

    def start(self):
        self.parent.start()

    def stop(self, result_flag=None):
        self.result_flag = result_flag
        self.parent.stop()


class Results(object):
    def __init__(self, total_results):
        self.results = [Result(self)] * total_results
        self.judge = None

    def __getitem__(self, index):
        return self.results[index]

    def link(self, judge):
        self.judge = judge
        self.packet_manager = packet.PacketManager("host", "port", self.judge)

    def run(self, input_files, output_files):
        self.packet_manager.begin_grading_packet()
        for result, input_file, output_file in zip(self.results, input_files, output_files):
            self.judge.run(result, input_file, output_file)
            self.packet_manager.test_case_status_packet(result.result_flag, result.elapsed_time, result.max_memory,
                                                        result.partial_output)
        self.packet_manager.grading_end_packet()

    def start(self):
        pass

    def stop(self):
        pass


class Judge(object):
    EOF = ""

    def __init__(self, processname, language="", redirect=False, transfer=False, interact=False, results=None):
        self.processname = processname
        self.language = language
        self.redirect = redirect
        self.transfer = transfer
        self.interact = interact
        self.results = results
        self.old_stdin = sys.stdin
        self.old_stdout = sys.stdout
        self.current_submission = None
        if self.redirect:
            sys.stdin = self
            sys.stdout = self
        self.results.link(self)

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
                self.result.stop(result_flag)
                self.write_lock.acquire()
        return not self.stopped

    def close(self, force_terminate=False, result_flag=None):
        if self.alive(result_flag):
            self.result.stop(result_flag)
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

    def run(self, result, input_file, output_file):
        self.exitcode = None
        self.stopped = False
        self.write_queue = Queue.Queue()
        self.write_lock = threading.Lock()
        self.process = execute.execute(self.processname)
        self.result = result
        self.result.start()
        if self.transfer:
            self.write(sys.stdin.read())
        thread.start_new_thread(self.write_async, (self.write_lock,))
        result_flag = 0
        with open(input_file, "r") as fi, open(output_file, "r") as fo:
            self.write(fi.read().strip())
            self.write(Judge.EOF)
            process_output = self.read().strip().replace('\r\n', '\n')
            self.result.give_partial_output(process_output[:10])
            self.result.max_memory = self.process.get_max_memory()
            self.result.elapsed_time = self.process.get_execution_time()
            judge_output = fo.read().strip().replace('\r\n', '\n')
            if process_output != judge_output:
                result_flag |= Result.WA
        self.close(result_flag=result_flag)

    def write(self, data):
        self.write_queue.put_nowait(data)

    def write_async(self, write_lock):
        try:
            while True:
                while write_lock.acquire(False) and self.alive():
                    write_lock.release()
                    try:
                        data = self.write_queue.get(False, 1)
                        break
                    except:
                        pass
                else:
                    break
                if data == Judge.EOF:
                    self.process.stdin.close()
                    break
                else:
                    data = data.replace('\r\n', '\n').replace('\r', '\n')
                    self.process.stdin.write(data)
                    if data == '\n':
                        self.process.stdin.flush()
                        os.fsync(self.process.stdin.fileno())
        except:
            pass

    def begin_grading(self, problem_id, language, source_code):
        pass


def main():
    if len(sys.argv) < 2:
        print "Invalid arguments"
        #sys.exit()
        #sys.argv.append("Rivers.exe")
    res = Results(1)
    with Judge([sys.executable, "aplusb.py"], redirect=False, interact=False, results=res) as judge:
        try:
            res.run(["aplusb.in"], ["aplusb.out"])
        except Exception, e:
            print e
    print res[0].elapsed_time, "seconds"
    print res[0].max_memory / 1024.0, "MB"
    if res[0].result_flag & Result.WA:
        print "Wrong Answer"
    else:
        print "Accepted"
    print "Done"


if __name__ == "__main__":
    main()
