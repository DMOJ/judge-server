import sys
import subprocess

import six

from dmoj.utils.unicode import utf8text

if six.PY2 and sys.platform == 'win32':
    import _subprocess
    from types import FunctionType, CodeType

    from ctypes import byref, windll, c_void_p, Structure, sizeof, c_wchar, WinError, POINTER
    from ctypes.wintypes import BYTE, WORD, LPWSTR, BOOL, DWORD, LPVOID, HANDLE

    CREATE_UNICODE_ENVIRONMENT = 0x00000400
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


    # Using LoadLibrary to avoid our argtypes conflicting.
    CreateProcessW = windll.LoadLibrary('kernel32.dll').CreateProcessW
    CreateProcessW.argtypes = [
        LPWSTR, LPWSTR, LPSECURITY_ATTRIBUTES,
        LPSECURITY_ATTRIBUTES, BOOL, DWORD, LPVOID, LPWSTR,
        LPSTARTUPINFOW, LPPROCESS_INFORMATION,
    ]
    CreateProcessW.restype = BOOL


    def CreateProcess(executable, args, _p_attr, _t_attr,
                      inherit_handles, creation_flags, env, cwd,
                      startup_info):
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
                          wenv, utf8text(cwd), byref(si), byref(pi)):
            return (WindowsHandle(pi.hProcess), WindowsHandle(pi.hThread),
                    pi.dwProcessId, pi.dwThreadId)
        raise WinError()


    class FakeSubprocess(object):
        def __getattribute__(self, item):
            if item == 'CreateProcess':
                return CreateProcess
            else:
                return getattr(_subprocess, item)


    def replace_globals(function, new_globals):
        func_globals = function.func_globals.copy()
        func_globals.update(new_globals)
        return FunctionType(function.func_code, func_globals, function.func_name,
                            function.func_defaults, function.func_closure)


    def replace_consts(function, new_consts):
        code = function.func_code
        consts = tuple(new_consts.get(const, const) for const in code.co_consts)
        new_code = CodeType(code.co_argcount, code.co_nlocals, code.co_stacksize, code.co_flags,
                            code.co_code, consts, code.co_names, code.co_varnames, code.co_filename,
                            code.co_name, code.co_firstlineno, code.co_lnotab, code.co_freevars,
                            code.co_cellvars)
        function.func_code = new_code


    class Popen(subprocess.Popen):
        _execute_child = replace_globals(subprocess.Popen._execute_child.im_func, {
            '_subprocess': FakeSubprocess(),
        })
        replace_consts(_execute_child, {'{} /c "{}"': u'{} /c "{}"'})


    call = replace_globals(subprocess.call, {'Popen': Popen})
    check_call = replace_globals(subprocess.check_call, {'call': call})
    check_output = replace_globals(subprocess.check_output, {'Popen': Popen})
else:
    Popen = subprocess.Popen
    call = subprocess.call
    check_call = subprocess.check_call
    check_output = subprocess.check_output
