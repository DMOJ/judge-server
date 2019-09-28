import logging

log = logging.getLogger('dmoj.cptbox')


def print_protection_fault(fault):
    syscall, callname, args = fault
    log.warning('Protection fault on: %d (%s)', syscall, callname)
    for i, arg in enumerate(args):
        log.warning('Arg%d: 0x%016x', i, arg)
