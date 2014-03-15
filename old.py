#!/usr/bin/python
import os, Queue, subprocess, sys, thread, threading, time


class Result():
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.elasped_time = None
        self.max_memory = None

    def start(self):
        self.start_time = time.clock()

    def stop(self):
        self.end_time = time.clock()
        self.elasped_time = self.end_time - self.start_time

    def memory_hook(self, lock, function, *args):
        while lock.acquire(False):
            self.update_memory(function(*args))
            lock.release()
            time.sleep(0.1)

    def update_memory(self, new_memory):
        if new_memory > self.max_memory:
            self.max_memory = new_memory


class Judge():
    def __init__(self, processname, language="", redirect=False, transfer=False, interact=False, result=None):
        if sys.platform == "win32":
            import memory  # @UnresolvedImport

            self.memory = memory
        self.process = subprocess.Popen([processname], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
        if result is not None:
            self.memory_lock = threading.Lock()
            result.start()
            thread.start_new_thread(result.memory_hook, (self.memory_lock, self.max_memory_usage,))
        self.result = result
        if transfer:
            self.write(sys.stdin.read())
        if redirect:
            self.old_stdin = sys.stdin
            self.old_stdout = sys.stdout
            sys.stdin = self
            sys.stdout = self
        self.exitcode = None
        self.stopped = False
        if interact:
            self.read_queue = Queue.Queue()
            thread.start_new_thread(self.read_async, ())
        self.interact = interact
        self.write_queue = Queue.Queue()
        thread.start_new_thread(self.write_async, ())

    def __del__(self):
        if self.alive():
            if self.result is not None:
                self.result.stop()
                self.result.update_memory(self.max_memory_usage())
                self.memory_lock.acquire()
            sys.stdin = self.old_stdin
            sys.stdout = self.old_stdout
            self.process.terminate()
            self.stopped = True

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    def alive(self):
        if not self.stopped:
            self.exitcode = self.process.poll()
            if self.exitcode is not None:
                sys.stdin = self.old_stdin
                sys.stdout = self.old_stdout
                self.stopped = True
                if self.result is not None:
                    self.result.stop()
                    self.memory_lock.acquire()
        return not self.stopped

    def close(self):
        if self.alive():
            if self.result is not None:
                self.result.stop()
                self.result.update_memory(self.max_memory_usage())
                self.memory_lock.acquire()
            sys.stdin = self.old_stdin
            sys.stdout = self.old_stdout
            if self.interact:
                self.process.terminate()
            else:
                self.exitcode = self.process.wait()
            self.stopped = True

    def read(self, *args):
        return self.process.stdout.read(*args) if self.alive() else ""

    def readline(self):
        while True:
            while self.alive():
                try:
                    data = self.read_queue.get()
                    data = data.rstrip().replace('\r\n', '\n').replace('\r', '\n')
                    if data:
                        return data
                except:
                    pass
            else:
                break
        return ""

    def read_async(self):
        try:
            while True:
                while self.alive():
                    try:
                        data = self.process.stdout.readline()
                        if data:
                            break
                    except:
                        pass
                else:
                    break
                self.read_queue.put_nowait(data)
        except:
            pass

    def write(self, data):
        self.write_queue.put_nowait(data)

    def write_async(self):
        try:
            while True:
                while self.alive():
                    try:
                        data = self.write_queue.get(False, 1)
                        break
                    except:
                        pass
                else:
                    break
                data = data.replace('\r\n', '\n').replace('\r', '\n')
                self.process.stdin.write(data)
                if data == '\n':
                    self.process.stdin.flush()
                    os.fsync(self.process.stdin.fileno())
        except:
            pass

    def max_memory_usage(self):
        return \
            self.memory.get_memory_info(
                self.memory.OpenProcess(self.memory.PROCESS_ALL_ACCESS, True, self.process.pid))[
                "PeakPagefileUsage"]  # @UndefinedVariable


def main():
    if len(sys.argv) < 2:
        print "Invalid arguments"
        #sys.exit()
        #sys.argv.append("Rivers.exe")
        sys.argv.append("Segment_Tree_Test.exe")
    res = Result()
    with open("aplusb.in", "r") as fi:
        data = fi.read()
    with Judge(sys.argv[1], redirect=True, interact=False, result=res) as process:
        try:
            print
            data.strip()
            with open("aplusb.out", "r") as fo:
                '''
                # interact
                for line in fo:
                    line=line.rstrip()
                    if not line:
                        break
                    output=raw_input()
                    if line!=output:
                        print>>sys.__stdout__, "Mismatch"
                '''
                # normal
                judge = fo.read().rstrip().replace('\r\n', '\n')
                user = process.read().rstrip().replace('\r\n', '\n')
                if judge != user:
                    print >> sys.__stdout__, "Mismatch"
        except Exception, e:
            print >> process.old_stdout, e
    print
    res.elasped_time, "seconds"
    print
    res.max_memory / 1024.0 / 1024.0, "MB"
    print
    "Done"


main()
