from _cptbox import Process
import sys
import os


class MyProcess(Process):
    def _callback(self, syscall):
        if syscall == 5:
            print 'Access:', self.debugger.readstr(self.debugger.uarg0)
        elif syscall == 102:
            print 'Socket call'
            self.debugger.syscall = 20
            self.debugger.on_return(self.socket_return)
        return True

    def socket_return(self):
        print 'Returned from: %d: %016x' % (self.debugger.syscall, self.debugger.result)
        assert self.debugger.result == self.debugger.getpid()


def main():
    proc = MyProcess(32)
    for call in xrange(341):
        proc._handler(call, 1)
    proc._handler(5, 2)
    proc._handler(102, 2)
    proc._spawn(sys.executable, ['python', os.path.join(os.path.dirname(__file__), 'cptbox_test_slave.py')])
    print 'Return: %d' % proc._monitor()
    print 'Memory usage: %d KB' % proc.max_memory

if __name__ == '__main__':
    main()