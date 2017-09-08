import sys


def print_protection_fault(fault, stream=sys.stderr):
    syscall, callname, args = fault
    print>> stream, 'Protection fault on: %d (%s)' % (syscall, callname)
    print>> stream, 'Arg0: 0x%016x' % args[0]
    print>> stream, 'Arg1: 0x%016x' % args[1]
    print>> stream, 'Arg2: 0x%016x' % args[2]
    print>> stream, 'Arg3: 0x%016x' % args[3]
    print>> stream, 'Arg4: 0x%016x' % args[4]
    print>> stream, 'Arg5: 0x%016x' % args[5]
