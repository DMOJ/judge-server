from __future__ import print_function

from subprocess import list2cmdline, Popen
import os

import six
from dmoj.wbox._wbox import UserManager, ProcessManager, NetworkManager, \
    update_address_x86, update_address_x64
from dmoj.utils.winutils import execution_time
from dmoj.utils.communicate import safe_communicate as _safe_communicate
from dmoj.judgeenv import env as judge_config
import ctypes
import sys


def unicodify(path):
    if path is None:
        return None
    if isinstance(path, six.text_type):
        return path
    return path.decode('mbcs')


dirname = os.path.dirname(__file__)
update_address_x86(os.path.join(dirname, u'getaddr32.exe'))
update_address_x64(os.path.join(dirname, u'getaddr64.exe'))


class WBoxPopen(object):
    def __init__(self, argv, time, memory, nproc=1, executable=None, cwd=None, env=None,
                 network_block=False, inject32=None, inject64=None, inject_func=None):
        username = u'wboxusr_%s' % judge_config.id
        if not ctypes.windll.netapi32.NetUserDel(None, username):
            print("found uncleaned wbox user '%s'; deleted." % username, file=sys.stderr)
        self.user = UserManager(username)

        self.process = ProcessManager(self.user.username, self.user.password)
        self.process.command = unicodify(list2cmdline(argv))
        if executable is not None:
            self.process.executable = unicodify(executable)
        if cwd is not None:
            self.process.dir = unicodify(cwd)
        if env is not None:
            self.process.set_environment(self._encode_environment(env))
        self.process.time_limit = time
        self.process.memory_limit = memory * 1024
        self.process.process_limit = nproc
        if inject32 is not None:
            self.process.inject32 = unicodify(inject32)
        if inject64 is not None:
            self.process.inject64 = unicodify(inject64)
        if inject_func is not None:
            self.process.inject_func = str(inject_func)
        self.returncode = None
        self.universal_newlines = False
        if executable is not None and network_block:
            # INetFwRules expects \, not / in paths, and fails with E_INVALIDARG if a path contains \
            # (even though this is valid in most other places in Windows)
            # See https://github.com/DMOJ/judge/issues/166 for more details
            executable.replace('/', '\\')
            self.network_block = NetworkManager('wbox_%s' % judge_config.id, executable)
        else:
            self.network_block = None
        self.process.spawn()

    @staticmethod
    def _encode_environment(env):
        buf = []
        for key, value in six.iteritems(env):
            buf.append(u'%s=%s' % (unicodify(key), unicodify(value)))
        return u'\0'.join(buf) + u'\0\0'

    def wait(self, timeout=None):
        self.process.wait(timeout)
        return self.poll()

    def poll(self):
        self.returncode = self.process.get_exit_code()
        if self.returncode is not None and self.network_block is not None:
            self.network_block.dispose()
        return self.returncode

    def kill(self, code=0xDEADBEEF):
        self.process.terminate(code)

    @property
    def stdin(self):
        return self.process.stdin

    @property
    def stdout(self):
        return self.process.stdout

    @property
    def stderr(self):
        return self.process.stderr

    @property
    def mle(self):
        return self.process.mle

    @property
    def max_memory(self):
        return self.process.memory / 1024.

    @property
    def max_memory_bytes(self):
        return self.process.memory

    @property
    def tle(self):
        return self.process.tle

    @property
    def execution_time(self):
        return self.process.execution_time

    @property
    def cpu_time(self):
        return execution_time(self.process._handle)

    @property
    def r_execution_time(self):
        return self.process.execution_time

    def communicate(self, stdin=None):
        return self._communicate(stdin)

    _communicate = Popen._communicate.im_func
    _readerthread = Popen._readerthread.im_func

    safe_communicate = _safe_communicate
