import abc
import os
import re
import shutil
import sys
from typing import Any, List, Tuple, Union

from dmoj.cptbox import IsolateTracer, TracedPopen, syscalls
from dmoj.cptbox.handlers import ALLOW
from dmoj.error import InternalError
from dmoj.judgeenv import env
from dmoj.utils import setbufsize_path
from dmoj.utils.unicode import utf8bytes

BASE_FILESYSTEM = ['/dev/(?:null|tty|zero|u?random)$',
                   '/usr/(?!home)', '/lib(?:32|64)?/', '/opt/', '/etc$',
                   '/etc/(?:localtime|timezone|nsswitch.conf|resolv.conf|passwd|malloc.conf)$',
                   '/usr$', '/tmp$', '/$']
BASE_WRITE_FILESYSTEM = ['/dev/stdout$', '/dev/stderr$', '/dev/null$']

if 'freebsd' in sys.platform:
    BASE_FILESYSTEM += [r'/etc/s?pwd\.db$', '/dev/hv_tsc$']
else:
    BASE_FILESYSTEM += ['/sys/devices/system/cpu(?:$|/online)',
                        '/etc/selinux/config$']

if sys.platform.startswith('freebsd'):
    BASE_FILESYSTEM += [r'/etc/libmap\.conf$', r'/var/run/ld-elf\.so\.hints$']
else:
    # Linux and kFreeBSD mounts linux-style procfs.
    BASE_FILESYSTEM += ['/proc$', '/proc/(?:self|{pid})/(?:maps|exe|auxv)$',
                        '/proc/(?:self|{pid})$',
                        '/proc/(?:meminfo|stat|cpuinfo|filesystems|xen|uptime)$',
                        '/proc/sys/vm/overcommit_memory$']

    # Linux-style ld.
    BASE_FILESYSTEM += [r'/etc/ld\.so\.(?:nohwcap|preload|cache)$']


class PlatformExecutorMixin(metaclass=abc.ABCMeta):
    address_grace = 65536
    data_grace = 0
    fsize = 0
    personality = 0x0040000  # ADDR_NO_RANDOMIZE
    fs: List[str] = []
    write_fs: List[str] = []
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
        name = self.get_executor_name()
        fs = BASE_FILESYSTEM + self.fs + env.get('extra_fs', {}).get(name, []) + [re.escape(self._dir)]
        return fs

    def get_write_fs(self):
        return BASE_WRITE_FILESYSTEM + self.write_fs

    def get_allowed_syscalls(self):
        return self.syscalls

    def get_address_grace(self):
        return self.address_grace

    def get_env(self):
        env = {'LANG': 'C.UTF-8'}
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

        return TracedPopen([utf8bytes(a) for a in self.get_cmdline() + list(args)],
                           executable=utf8bytes(self.get_executable()),
                           security=self.get_security(launch_kwargs=kwargs),
                           address_grace=self.get_address_grace(),
                           data_grace=self.data_grace,
                           personality=self.personality,
                           fds=kwargs.get('fds'),
                           time=kwargs.get('time'),
                           memory=kwargs.get('memory'),
                           wall_time=kwargs.get('wall_time'),
                           stdin=kwargs.get('stdin'),
                           stdout=kwargs.get('stdout'),
                           stderr=kwargs.get('stderr'),
                           env=env, cwd=utf8bytes(self._dir),
                           nproc=self.get_nproc(),
                           fsize=self.fsize)


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


class ScriptDirectoryMixin:
    """
    Certain script executors need access to the entire directory of the script,
    usually for some searching purposes.
    """

    def get_fs(self):
        return super().get_fs() + [self._dir]
