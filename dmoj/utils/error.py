import errno
import logging
import os
from typing import List, Optional, Tuple

log = logging.getLogger('dmoj.cptbox')


def print_protection_fault(fault: Tuple[int, str, List[int], Optional[int]]) -> None:
    syscall, callname, args, update_errno = fault
    if update_errno is not None:
        log.warning(
            'Failed to alter system call: %d (%s) with error %d (%s): %s',
            syscall,
            callname,
            update_errno,
            errno.errorcode[update_errno],
            os.strerror(update_errno),
        )
    else:
        log.warning('Protection fault on: %d (%s)', syscall, callname)
    for i, arg in enumerate(args):
        log.warning('Arg%d: 0x%016x', i, arg)
