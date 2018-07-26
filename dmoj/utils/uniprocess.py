# Work around Python 2 not being able to use Unicode command lines on Windows.
import copy
import sys
from subprocess import Popen as OldPopen

import six

if six.PY2 and sys.platform == 'win32':
    import _subprocess

    # Based on https://gist.github.com/vaab/2ad7051fc193167f15f85ef573e54eb9.
    from ctypes import byref, windll, c_char_p, c_wchar_p, c_void_p, Structure, sizeof, c_wchar, WinError, POINTER
    from ctypes.wintypes import BYTE, WORD, LPWSTR, BOOL, DWORD, LPVOID, HANDLE

    CREATE_UNICODE_ENVIRONMENT = 0x00000400
    LPCTSTR = c_char_p
    LPTSTR = c_wchar_p
    LPSECURITY_ATTRIBUTES = c_void_p
    LPBYTE = POINTER(BYTE)


    class STARTUPINFOW(Structure):
        _fields_ = [
            ('cb', DWORD), ('lpReserved', LPWSTR),
            ('lpDesktop', LPWSTR), ('lpTitle', LPWSTR),
            ('dwX', DWORD), ('dwY', DWORD),
            ('dwXSize', DWORD), ('dwYSize', DWORD),
            ('dwXCountChars', DWORD), ('dwYCountChars', DWORD),
            ('dwFillAtrribute', DWORD), ('dwFlags', DWORD),
            ('wShowWindow', WORD), ('cbReserved2', WORD),
            ('lpReserved2', LPBYTE), ('hStdInput', HANDLE),
            ('hStdOutput', HANDLE), ('hStdError', HANDLE),
        ]


    LPSTARTUPINFOW = POINTER(STARTUPINFOW)


    class PROCESS_INFORMATION(Structure):
        _fields_ = [
            ('hProcess', HANDLE), ('hThread', HANDLE),
            ('dwProcessId', DWORD), ('dwThreadId', DWORD),
        ]


    LPPROCESS_INFORMATION = POINTER(PROCESS_INFORMATION)


    class WindowsHandle(c_void_p):
        """Emulate the handle objects in _subprocess."""

        def __init__(self, *a, **kw):
            super(WindowsHandle, self).__init__(*a, **kw)
            self.closed = False

        def Close(self):
            if not self.closed:
                windll.kernel32.CloseHandle(self)
                self.closed = True

        def __int__(self):
            return self.value


    CreateProcessW = windll.kernel32.CreateProcessW
    CreateProcessW.argtypes = [
        LPCTSTR, LPTSTR, LPSECURITY_ATTRIBUTES,
        LPSECURITY_ATTRIBUTES, BOOL, DWORD, LPVOID, LPCTSTR,
        LPSTARTUPINFOW, LPPROCESS_INFORMATION,
    ]
    CreateProcessW.restype = BOOL


    def CreateProcess(executable, args, _p_attr, _t_attr,
                      inherit_handles, creation_flags, env, cwd,
                      startup_info):
        """Create a process supporting unicode executable and args for win32
        Python implementation of CreateProcess using CreateProcessW for Win32
        """

        int_or_none = lambda x: None if x is None else int(x)

        si = STARTUPINFOW(
            dwFlags=startup_info.dwFlags,
            wShowWindow=startup_info.wShowWindow,
            cb=sizeof(STARTUPINFOW),
            hStdInput=int_or_none(startup_info.hStdInput),
            hStdOutput=int_or_none(startup_info.hStdOutput),
            hStdError=int_or_none(startup_info.hStdError),
        )

        wenv = None
        if env is not None:
            env = (u''.join(u'%s=%s\0' % (k, v) for k, v in env.items())) + u'\0'
            wenv = (c_wchar * len(env))()
            wenv.value = env

        pi = PROCESS_INFORMATION()
        creation_flags |= CREATE_UNICODE_ENVIRONMENT

        if CreateProcessW(executable, args, None, None,
                          inherit_handles, creation_flags,
                          wenv, cwd, byref(si), byref(pi)):
            return (WindowsHandle(pi.hProcess), WindowsHandle(pi.hThread),
                    pi.dwProcessId, pi.dwThreadId)
        raise WinError()


    class FakeSubprocess(object):
        def __getattribute__(self, item):
            if item == 'CreateProcess':
                return CreateProcess
            else:
                return getattr(_subprocess, item)


    class Popen(OldPopen):
        _execute_child = copy.deepcopy(OldPopen._execute_child.im_func)
        _execute_child.func_globals['_subprocess'] = FakeSubprocess()
else:
    Popen = OldPopen
