import re
from urllib2 import urlopen
from contextlib import closing

from syscall_tables import *

from __future__ import print_function

func_to_name = {}

with open('linux-x86.tbl', 'w') as x86, closing(urlopen(LINUX_SYSCALLS_32)) as data:
    for line in data:
        if line.startswith('#') or line.isspace():
            continue
        syscall = line.split()
        name = syscall[2].strip('_')
        if len(syscall) > 3:
            func = syscall[3]
            func_to_name[func] = name
        print('%d\t%s' % (int(syscall[0]), name, file=x86)

with open('linux-x64.tbl', 'w') as x64, open('linux-x32.tbl', 'w') as x32, closing(urlopen(LINUX_SYSCALLS_64)) as data:
    for line in data:
        if line.startswith('#') or line.isspace():
            continue
        syscall = line.split()
        id = int(syscall[0])
        arch = syscall[1]
        name = syscall[2].strip('_')
        if arch in ('common', '64'):
            print('%d\t%s' % (id, name), file=x64)
        if arch in ('common', 'x32'):
            print('%d\t%s' % (id, name), file=x32)

rewas = re.compile(r'/\* was (sys_[a-z0-9_]+) \*/')
with open('linux-arm.tbl', 'w') as arm, closing(urlopen(LINUX_SYSCALLS_ARM)) as data:
    id = 0
    for line in data:
        if 'CALL' in line:
            match = rewas.search(line)
            if match is None:
                func = line[line.rfind('(')+1:line.find(',') if ',' in line else line.find(')')]
            else:
                func = match.group(1)
            if func in func_to_name:
                name = func_to_name[func]
            else:
                name = func.replace('sys_', '').replace('_wrapper', '')
            if name != 'ni_syscall':
                print('%d\t%s' % (id, name), file=arm)
            id += 1
