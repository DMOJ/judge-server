from _cptbox import Process

allowed = [
    0, 1, 3, 5, 9, 10, 11, 12, 13, 14, 16, 21, 59, 72,
    78, 97, 137, 158, 202, 218, 231, 273,
]


class MyProcess(Process):
    def _callback(self, syscall):
        if syscall == 2:
            print 'Access:', self.debugger.readstr(self.debugger.uarg0)
        return True


def main():
    proc = MyProcess(64)
    for call in allowed:
        proc._handler(call, 1)
    proc._handler(2, 2)
    proc._spawn('/bin/ls', ['ls'])
    print 'Return: %d' % proc._monitor()
    print 'Memory usage: %d KB' % proc.max_memory

if __name__ == '__main__':
    main()