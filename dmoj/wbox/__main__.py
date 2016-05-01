import sys
import os

from dmoj.wbox.sandbox import WBoxPopen


def main():
    dir = os.path.dirname(__file__)

    print '        wbox Test Script'
    print '====Please run as administrator==='

    def run_file(file):
        print 'Running', file
        child = WBoxPopen(['python', os.path.join(dir, file)], 1, 16384, executable=sys.executable, network_block=True)
        print 'Result:', child.communicate()
        print 'Return:', child.returncode
        print 'Execution time:', child.execution_time
        print 'CPU time:', child.execution_time
        print 'Memory usage: {:,d} bytes ({:.2f} MiB)'.format(child.max_memory_bytes, child.max_memory / 1024.)
        print

    run_file('hello.py')
    run_file('hang.py')
    run_file('memory_abuse.py')
    run_file('google.py')

if __name__ == '__main__':
    main()