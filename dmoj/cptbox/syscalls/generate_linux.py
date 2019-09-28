import re
import codecs
from urllib.request import urlopen

utf8reader = codecs.getreader('utf-8')

LINUX_SYSCALLS_32 = 'https://raw.githubusercontent.com/torvalds/linux/master/arch/x86/entry/syscalls/syscall_32.tbl'
LINUX_SYSCALLS_64 = 'https://raw.githubusercontent.com/torvalds/linux/master/arch/x86/entry/syscalls/syscall_64.tbl'
LINUX_SYSCALLS_ARM = 'https://raw.githubusercontent.com/torvalds/linux/master/arch/arm/tools/syscall.tbl'
LINUX_SYSCALLS_GENERIC = 'https://raw.githubusercontent.com/torvalds/linux/master/include/uapi/asm-generic/unistd.h'

func_to_name = {}

with open('linux-x86.tbl', 'w') as x86, utf8reader(urlopen(LINUX_SYSCALLS_32)) as data:
    for line in data:
        if line.startswith('#') or line.isspace():
            continue
        syscall = line.split()
        name = syscall[2].strip('_')
        if len(syscall) > 3:
            func = syscall[3]
            func_to_name[func] = name
        if name == 'fstatat64':
            name = 'fstatat'
        print('%d\t%s' % (int(syscall[0]), name), file=x86)

with open('linux-x64.tbl', 'w') as x64, open('linux-x32.tbl', 'w') as x32, \
        utf8reader(urlopen(LINUX_SYSCALLS_64)) as data:
    for line in data:
        if line.startswith('#') or line.isspace():
            continue
        syscall = line.split()
        id = int(syscall[0])
        arch = syscall[1]
        name = syscall[2].strip('_')
        if name == 'newfstatat':
            name = 'fstatat'
        if arch in ('common', '64'):
            print('%d\t%s' % (id, name), file=x64)
        if arch in ('common', 'x32'):
            print('%d\t%s' % (id, name), file=x32)

rewas = re.compile(r'# (\d+) was (sys_[a-z0-9_]+)')
with open('linux-arm.tbl', 'w') as arm, utf8reader(urlopen(LINUX_SYSCALLS_ARM)) as data:
    id = 0
    for line in data:
        match = rewas.search(line)
        if match is None:
            if not line or line.startswith('#'):
                continue
            syscall = line.split()
            id = syscall[0]
            name = syscall[2].strip('_')
        else:
            id, func = match.groups()
            if func in func_to_name:
                name = func_to_name[func]
            else:
                name = func.replace('sys_', '').replace('_wrapper', '')
        if name == 'fstatat64':
            name = 'fstatat'
        print('%d\t%s' % (int(id), name), file=arm)

renr = re.compile('#define\s+__NR(?:3264)?_([a-z0-9_]+)\s+(\d+)')
with open('linux-generic.tbl', 'w') as generic, utf8reader(urlopen(LINUX_SYSCALLS_GENERIC)) as data:
    for line in data:
        if '#undef __NR_syscalls' in line:
            break
        match = renr.search(line)
        if match:
            name, id = match.groups()
            if name in ('arch_specific_syscall', 'sync_file_range2'):
                continue
            print('%d\t%s' % (int(id), name), file=generic)
