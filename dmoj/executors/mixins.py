import abc
import os
import re
import shutil
import sys
from typing import Any, List, Sequence, Tuple, Union

from dmoj.cptbox import IsolateTracer, TracedPopen, syscalls
from dmoj.cptbox.filesystem_policies import ExactDir, ExactFile, FilesystemAccessRule, RecursiveDir
from dmoj.cptbox.handlers import ALLOW
from dmoj.error import InternalError
from dmoj.judgeenv import env
from dmoj.utils import setbufsize_path
from dmoj.utils.unicode import utf8bytes

if os.path.isdir('/usr/home'):
    USR_DIR = [RecursiveDir(f'/usr/{d}') for d in os.listdir('/usr') if d != 'home' and os.path.isdir(f'/usr/{d}')]
else:
    USR_DIR = [RecursiveDir('/usr')]

BASE_FILESYSTEM = [
    ExactFile('/dev/null'),
    ExactFile('/dev/tty'),
    ExactFile('/dev/zero'),
    ExactFile('/dev/urandom'),
    ExactFile('/dev/random'),
    *USR_DIR,
    RecursiveDir('/lib'),
    RecursiveDir('/lib32'),
    RecursiveDir('/lib64'),
    RecursiveDir('/opt'),
    ExactDir('/etc'),
    ExactFile('/etc/localtime'),
    ExactFile('/etc/timezone'),
    ExactDir('/usr'),
    ExactDir('/tmp'),
    ExactDir('/'),
]

BASE_WRITE_FILESYSTEM = [ExactFile('/dev/null')]


if 'freebsd' in sys.platform:
    BASE_FILESYSTEM += [
        ExactFile('/etc/spwd.db'),
        ExactFile('/etc/pwd.db'),
        ExactFile('/dev/hv_tsc'),
        RecursiveDir('/dev/fd'),
    ]

else:
    BASE_FILESYSTEM += [
        ExactDir('/sys/devices/system/cpu'),
        ExactFile('/sys/devices/system/cpu/online'),
        ExactFile('/etc/selinux/config'),
    ]

if sys.platform.startswith('freebsd'):
    BASE_FILESYSTEM += [ExactFile('/etc/libmap.conf'), ExactFile('/var/run/ld-elf.so.hints')]
else:
    # Linux and kFreeBSD mounts linux-style procfs.
    BASE_FILESYSTEM += [
        ExactDir('/proc'),
        ExactDir('/proc/self'),
        ExactFile('/proc/self/maps'),
        ExactFile('/proc/self/exe'),
        ExactFile('/proc/self/auxv'),
        ExactFile('/proc/meminfo'),
        ExactFile('/proc/stat'),
        ExactFile('/proc/cpuinfo'),
        ExactFile('/proc/filesystems'),
        ExactDir('/proc/xen'),
        ExactFile('/proc/uptime'),
        ExactFile('/proc/sys/vm/overcommit_memory'),
    ]

    # Linux-style ld.
    BASE_FILESYSTEM += [ExactFile('/etc/ld.so.nohwcap'), ExactFile('/etc/ld.so.preload'), ExactFile('/etc/ld.so.cache')]

UTF8_LOCALE = 'C.UTF-8'

if sys.platform.startswith('freebsd') and sys.platform < 'freebsd13':
    UTF8_LOCALE = 'en_US.UTF-8'


class PlatformExecutorMixin(metaclass=abc.ABCMeta):
    address_grace = 65536
    data_grace = 0
    fsize = 0
    personality = 0x0040000  # ADDR_NO_RANDOMIZE
    fs: Sequence[FilesystemAccessRule] = []
    write_fs: Sequence[FilesystemAccessRule] = []
    syscalls: List[Union[str, Tuple[str, Any]]] = []

    def _add_syscalls(self, sec):
        for name in self.get_allowed_syscalls():
            if isinstance(name, tuple) and len(name) == 2:
                name, handler = name
            else:
                handler = ALLOW
            sec[getattr(syscalls, 'sys_' + name)] = handler
        return sec

    def get_security(self, launch_kwargs=None):
        sec = IsolateTracer(self.get_fs(), write_fs=self.get_write_fs())
        return self._add_syscalls(sec)

    def get_fs(self):
        return BASE_FILESYSTEM + self.fs + self._load_extra_fs() + [RecursiveDir(self._dir)]

    def _load_extra_fs(self):
        name = self.get_executor_name()
        extra_fs_config = env.get('extra_fs', {}).get(name, [])
        extra_fs = []
        constructors = dict(exact_file=ExactFile, exact_dir=ExactDir, recursive_dir=RecursiveDir)
        for rules in extra_fs_config:
            for type, path in rules.iteritems():
                constructor = constructors.get(type)
                assert constructor, f"Can't load rule for extra path with rule type {type}"
                extra_fs.append(constructor(path))

        return extra_fs

    def get_write_fs(self):
        return BASE_WRITE_FILESYSTEM + self.write_fs

    def get_allowed_syscalls(self):
        return self.syscalls

    def get_address_grace(self):
        return self.address_grace

    def get_env(self):
        env = {'LANG': UTF8_LOCALE}
        if self.unbuffered:
            env['CPTBOX_STDOUT_BUFFER_SIZE'] = 0
        return env

    def launch(self, *args, **kwargs):
        for src, dst in kwargs.get('symlinks', {}).items():
            src = os.path.abspath(os.path.join(self._dir, src))
            # Disallow the creation of symlinks outside the submission directory.
            if os.path.commonprefix([src, self._dir]) == self._dir:
                # If a link already exists under this name, it's probably from a
                # previous case, but might point to something different.
                if os.path.islink(src):
                    os.unlink(src)
                os.symlink(dst, src)
            else:
                raise InternalError('cannot symlink outside of submission directory')

        agent = self._file('setbufsize.so')
        shutil.copyfile(setbufsize_path, agent)
        env = {
            # Forward LD_LIBRARY_PATH for systems (e.g. Android Termux) that require
            # it to find shared libraries
            'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
            'LD_PRELOAD': agent,
            'CPTBOX_STDOUT_BUFFER_SIZE': kwargs.get('stdout_buffer_size'),
            'CPTBOX_STDERR_BUFFER_SIZE': kwargs.get('stderr_buffer_size'),
        }
        env.update(self.get_env())

        return TracedPopen(
            [utf8bytes(a) for a in self.get_cmdline(**kwargs) + list(args)],
            executable=utf8bytes(self.get_executable()),
            security=self.get_security(launch_kwargs=kwargs),
            address_grace=self.get_address_grace(),
            data_grace=self.data_grace,
            personality=self.personality,
            time=kwargs.get('time'),
            memory=kwargs.get('memory'),
            wall_time=kwargs.get('wall_time'),
            stdin=kwargs.get('stdin'),
            stdout=kwargs.get('stdout'),
            stderr=kwargs.get('stderr'),
            env=env,
            cwd=utf8bytes(self._dir),
            nproc=self.get_nproc(),
            fsize=self.fsize,
        )


class NullStdoutMixin:
    """
    Some compilers print a lot of debug info to stdout even with successful compiles. This mixin pipes that generally-
    useless data into os.devnull so that the user never sees it.
    """

    def __init__(self, *args, **kwargs):
        self._devnull = open(os.devnull, 'w')
        super().__init__(*args, **kwargs)

    def cleanup(self):
        if hasattr(self, '_devnull'):
            self._devnull.close()
        super().cleanup()

    def get_compile_popen_kwargs(self):
        result = super().get_compile_popen_kwargs()
        result['stdout'] = self._devnull
        return result


class SingleDigitVersionMixin:
    version_regex = re.compile(r'.*?(\d+(?:\.\d+)*)', re.DOTALL)
