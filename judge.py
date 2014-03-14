#!/usr/bin/python
import os, Queue, subprocess, sys, thread, threading, time

class Result(object):
    AC=0x0
    WA=0x1
    def __init__(self):
        self.start_time=None
        self.end_time=None
        self.elasped_time=None
        self.max_memory=None
        self.result_flag=None
    def start(self):
        self.start_time=time.clock()
    def stop(self, result_flag=None):
        self.end_time=time.clock()
        self.elasped_time=self.end_time-self.start_time
        self.result_flag=result_flag
    def memory_hook(self, lock, function, *args):
        while lock.acquire(False):
            self.update_memory(function(*args))
            lock.release()
            time.sleep(0.1)
    def update_memory(self, new_memory):
        if new_memory>self.max_memory:
            self.max_memory=new_memory

class Results(object):
    def __init__(self, total_results):
        self.results=[Result()]*total_results
        self.judge=None
    def __getitem__(self, index):
        return self.results[index]
    def link(self, judge):
        self.judge=judge
    def run(self, input_files, output_files):
        for result, input_file, output_file in zip(self.results, input_files, output_files):
            self.judge.run(result, input_file, output_file)

class Judge(object):
    EOF=""
    def __init__(self, processname, language="", redirect=False, transfer=False, interact=False, results=None):
        if sys.platform=="win32":
            import memory # @UnresolvedImport
            self.memory=memory
        self.processname=processname
        self.language=language
        self.redirect=redirect
        self.transfer=transfer
        self.interact=interact
        self.results=results
        self.old_stdin=sys.stdin
        self.old_stdout=sys.stdout
        self.current_submission=None
        if self.redirect:
            sys.stdin=self
            sys.stdout=self
        self.results.link(self)
    def __del__(self):
        self.close(True)
    def __enter__(self):
        return self
    def __exit__(self, exception_type, exception_value, traceback):
        self.close()
    def alive(self):
        if not self.stopped:
            self.exitcode=self.process.poll()
            if self.exitcode is not None:
                sys.stdin=self.old_stdin
                sys.stdout=self.old_stdout
                self.stopped=True
                self.result.stop()
                self.write_lock.acquire()
                self.memory_lock.acquire()
        return not self.stopped
    def close(self, force_terminate=False):
        if self.alive():
            self.result.stop()
            self.write_lock.acquire()
            self.result.update_memory(self.max_memory_usage())
            self.memory_lock.acquire()
            sys.stdin=self.old_stdin
            sys.stdout=self.old_stdout
            if force_terminate or self.interact:
                self.process.terminate()
            else:
                self.exitcode=self.process.wait()
            self.stopped=True
    def read(self, *args):
        return self.process.stdout.read(*args) if self.alive() else ""
    def readline(self):
        if not self.alive():
            return ""
        line=self.process.stdout.readline().rstrip()
        while not line and self.alive():
            line=self.process.stdout.readline().rstrip()
        return line.rstrip() if line else ""
    def run(self, result, input_file, output_file):
        self.exitcode=None
        self.stopped=False
        self.write_queue=Queue.Queue()
        self.write_lock=threading.Lock()
        self.memory_lock=threading.Lock()
        self.process=subprocess.Popen([self.processname], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.result=result
        self.result.start()
        thread.start_new_thread(result.memory_hook, (self.memory_lock, self.max_memory_usage,))
        if self.transfer:
            self.write(sys.stdin.read())
        thread.start_new_thread(self.write_async, (self.write_lock,))
        result_flag=0
        with open(input_file, "r") as fi, open(output_file, "r") as fo:
            self.write(fi.read().strip())
            self.write(Judge.EOF)
            process_output=self.read().strip().replace('\r\n', '\n')
            judge_output=fo.read().strip().replace('\r\n', '\n')
            if process_output!=judge_output:
                result_flag|=Result.WA
        self.close()
        self.stopped=True
        self.result.stop(result_flag)
    def write(self, data):
        self.write_queue.put_nowait(data)
    def write_async(self, write_lock):
        try:
            while True:
                while write_lock.acquire(False) and self.alive():
                    write_lock.release()
                    try:
                        data=self.write_queue.get(False, 1)
                        break
                    except:
                        pass
                else:
                    break
                if data==Judge.EOF:
                    self.process.stdin.close()
                    break
                else:
                    data=data.replace('\r\n', '\n').replace('\r', '\n')
                    self.process.stdin.write(data)
                    if data=='\n':
                        self.process.stdin.flush()
                        os.fsync(self.process.stdin.fileno())
        except:
            pass
    def max_memory_usage(self):
        return self.memory.get_memory_info(self.memory.OpenProcess(self.memory.PROCESS_ALL_ACCESS, True, self.process.pid))["PeakPagefileUsage"] # @UndefinedVariable
    def begin_grading(self, problem_id, language, source_code):
        pass

def main():
    if len(sys.argv)<2:
        print "Invalid arguments"
        #sys.exit()
        #sys.argv.append("Rivers.exe")
        sys.argv.append("Segment_Tree_Test.exe")
    res=Results(1)
    with Judge(sys.argv[1], redirect=False, interact=False, results=res) as judge:
        try:
            res.run(["segtree10.in"], ["segtree10.out"])
        except Exception, e:
            print e
    print res[0].elasped_time, "seconds"
    print res[0].max_memory/1024.0/1024.0, "MB"
    if res[0].result_flag&Result.WA:
        print "Wrong Answer"
    else:
        print "Accepted"
    print "Done"

if __name__=="__main__":
    main()
