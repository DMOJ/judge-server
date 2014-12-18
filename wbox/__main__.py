from sandbox import WBoxPopen
import sys
import os


def main():
    dir = os.path.dirname(__file__)

    def run_file(file):
        print 'Running', file
        child = WBoxPopen(['python', os.path.join(dir, file)], 1, 16384, executable=sys.executable)
        print 'Result:', child.communicate()
        print 'Return:', child.returncode
        print 'Execution time:', child.execution_time
        print 'CPU time:', child.execution_time
        print 'Memory usage: {:,d} bytes ({:.2f} MiB)'.format(child.max_memory_bytes, child.max_memory / 1024.)
        print

    run_file('hello.py')
    run_file('hang.py')
    run_file('memory_abuse.py')

if __name__ == '__main__':
    main()