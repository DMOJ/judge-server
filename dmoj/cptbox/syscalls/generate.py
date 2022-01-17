import codecs
import re
from urllib.request import urlopen

utf8reader = codecs.getreader('utf-8')

LINUX_SYSCALLS_32 = 'https://raw.githubusercontent.com/torvalds/linux/master/arch/x86/entry/syscalls/syscall_32.tbl'
LINUX_SYSCALLS_64 = 'https://raw.githubusercontent.com/torvalds/linux/master/arch/x86/entry/syscalls/syscall_64.tbl'
LINUX_SYSCALLS_ARM = 'https://raw.githubusercontent.com/torvalds/linux/master/arch/arm/tools/syscall.tbl'
LINUX_SYSCALLS_GENERIC = 'https://raw.githubusercontent.com/torvalds/linux/master/include/uapi/asm-generic/unistd.h'
FREEBSD_SYSCALLS = 'https://cgit.freebsd.org/src/plain/sys/kern/syscalls.master'

func_to_name = {}
names = set()

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
        names.add(name)
        print('%d\t%s' % (int(syscall[0]), name), file=x86)

with open('linux-x64.tbl', 'w') as x64, open('linux-x32.tbl', 'w') as x32, utf8reader(
    urlopen(LINUX_SYSCALLS_64)
) as data:
    for line in data:
        if line.startswith('#') or line.isspace():
            continue
        syscall = line.split()
        id = int(syscall[0])
        arch = syscall[1]
        name = syscall[2].strip('_')
        if name == 'newfstatat':
            name = 'fstatat'
        names.add(name)
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
            id_str = syscall[0]
            name = syscall[2].strip('_')
        else:
            id_str, func = match.groups()
            if func in func_to_name:
                name = func_to_name[func]
            else:
                name = func.replace('sys_', '').replace('_wrapper', '')
        if name == 'fstatat64':
            name = 'fstatat'
        names.add(name)
        print('%d\t%s' % (int(id_str), name), file=arm)

renr = re.compile(r'#define\s+__NR(?:3264)?_([a-z0-9_]+)\s+(\d+)')
with open('linux-generic.tbl', 'w') as generic64, open('linux-generic32.tbl', 'w') as generic32, utf8reader(
    urlopen(LINUX_SYSCALLS_GENERIC)
) as data:
    only_32 = False
    for line in data:
        if '#undef __NR_syscalls' in line:
            break
        if '#if __BITS_PER_LONG == 32' in line:
            only_32 = True
            continue
        if '#endif' in line:
            only_32 = False
        match = renr.search(line)
        if match:
            name, id_str = match.groups()
            id = int(id_str)
            if name in ('arch_specific_syscall', 'sync_file_range2'):
                continue
            names.add(name)
            if not only_32:
                print('%d\t%s' % (id, name), file=generic64)
            print('%d\t%s' % (id, name), file=generic32)


renumber = re.compile(r'^(\d+)\s+AUE_\S+\s+\S+(?:\t(\w+)$)?')
rename = re.compile(r'\t\t\w+ \*?(.*)\(')
number = -1


def freebsd_syscall(name):
    global number
    if number == -1:
        raise RuntimeError('FreeBSD line missed?')
    name = name.lstrip('_')
    names.add(name)
    print(f'{number}\t{name}', file=output)
    number = -1


with open('freebsd.tbl', 'w') as output, utf8reader(urlopen(FREEBSD_SYSCALLS)) as data:
    for line in data:
        match = renumber.match(line)
        if match:
            number = int(match[1])
            if match[2]:
                freebsd_syscall(match[2])
        else:
            match = rename.match(line)
            if match:
                freebsd_syscall(match[1])

with open('aliases.list') as aliases:
    for line in aliases:
        names.add(line.split()[1])

with open('../syscalls.pyi', 'w') as interface:
    print(
        """\
from typing import List, Dict, Tuple

translator: List[Tuple[List[int], ...]]
by_name: Dict[str, int]
by_id: List[str]
SYSCALL_COUNT: int
""",
        file=interface,
    )
    for name in sorted(names):
        print('sys_%s: int' % (name,), file=interface)
