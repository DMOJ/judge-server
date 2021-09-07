import os
from typing import List, Tuple

order = [
    'linux-x86.tbl',
    'linux-x64.tbl',
    'linux-x32.tbl',
    'linux-arm.tbl',
    'freebsd.tbl',
    'linux-generic.tbl',
    'linux-generic32.tbl',
]
max_id = 0
by_name = {}
by_id: List[str] = []
__all__: List[str] = by_id
translator: List[Tuple[List[int], ...]]


def create():
    global max_id, translator

    dir = os.path.join(os.path.dirname(__file__), 'syscalls')
    size = len(order)

    iid_map = {}

    with open(os.path.join(dir, 'aliases.list')) as f:
        for i, line in enumerate(f):
            names = line.split()
            by_id.append('sys_' + names[0])
            iid_map[i] = [[] for _ in range(size)]
            for call in names:
                by_name[call] = i

    max_id = max(by_name.values())

    def alloc_id(name):
        global max_id
        if name in by_name:
            return by_name[name]
        max_id += 1
        by_name[name] = max_id
        by_id.append('sys_' + name)
        iid_map[max_id] = [[] for _ in range(size)]
        return max_id

    for i, file in enumerate(order):
        with open(os.path.join(dir, file)) as f:
            for line in f:
                id, name = line.split()
                key = alloc_id(name)
                iid_map[key][i].append(int(id))

    max_id += 1
    blank = (None,) * size
    translator = [blank] * max_id
    for id, data in iid_map.items():
        translator[id] = tuple(data)

    for name, id in list(by_name.items()):
        key = 'sys_' + name
        globals()[key] = by_name[key] = id


create()
SYSCALL_COUNT = max_id
del create, os, max_id
