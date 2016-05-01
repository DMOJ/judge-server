from ctypes.wintypes import *
from ctypes import *
import ctypes

_kernel32 = ctypes.windll.kernel32
_ole32 = ctypes.windll.ole32
_oleaut32 = ctypes.windll.oleaut32
_netapi32 = ctypes.windll.netapi32
_advapi32 = ctypes.windll.advapi32

CreateJobObject = _kernel32.CreateJobObjectW
CreateProcess = _kernel32.CreateProcessW
AssignProcessToJobObject = _kernel32.AssignProcessToJobObject
ResumeThread = _kernel32.ResumeThread
CloseHandle = _kernel32.CloseHandle
WaitForSingleObject = _kernel32.WaitForSingleObject
TerminateProcess = _kernel32.TerminateProcess
SetInformationJobObject = _kernel32.SetInformationJobObject
QueryInformationJobObject = _kernel32.QueryInformationJobObject
GetCurrentProcess = _kernel32.GetCurrentProcess
CreateIoCompletionPort = _kernel32.CreateIoCompletionPort
DuplicateHandle = _kernel32.DuplicateHandle

DuplicateHandle.argtypes = [HANDLE, HANDLE, HANDLE, POINTER(HANDLE), DWORD, BOOL, DWORD]
GetCurrentProcess.restype = HANDLE

CreateIoCompletionPort.argtypes = [HANDLE, HANDLE, LPVOID, DWORD]
CreateIoCompletionPort.restype = HANDLE


def CreatePipe(buf=0):
    read, write = HANDLE(), HANDLE()
    if not _kernel32.CreatePipe(byref(read), byref(write), None, buf):
        raise WinError()
    return read.value, write.value


def make_inheritable(handle):
    out = HANDLE()
    DuplicateHandle(GetCurrentProcess(), handle, GetCurrentProcess(), byref(out), 0, True,
                    DUPLICATE_CLOSE_SOURCE | DUPLICATE_SAME_ACCESS)
    return out.value


def GetExitCodeProcess(process):
    code = DWORD()
    if not _kernel32.GetExitCodeProcess(process, byref(code)):
        raise WinError()
    return None if code.value == 259 else code.value


LPSTR = ctypes.c_char_p
LPBYTE = LPSTR
LPWSTR = ctypes.c_wchar_p
LPHANDLE = POINTER(HANDLE)
LPDWORD = POINTER(DWORD)

NULL = None
TRUE = 1
FALSE = 0

TOKEN_ASSIGN_PRIMARY = 0x0001
TOKEN_DUPLICATE = 0x0002
TOKEN_IMPERSONATE = 0x0004
TOKEN_QUERY = 0x0008
TOKEN_QUERY_SOURCE = 0x0010
TOKEN_ADJUST_PRIVILEGES = 0x0020
TOKEN_ADJUST_GROUPS = 0x0040
TOKEN_ADJUST_DEFAULT = 0x0080
TOKEN_ADJUST_SESSIONID = 0x0100

SecurityAnonymous = 0
SecurityIdentification = 1
SecurityImpersonation = 2
SecurityDelegation = 3

TokenPrimary = 1
TokenImpersonation = 2

ERROR_BROKEN_PIPE = 109
INVALID_HANDLE_VALUE = -1
HANDLE_FLAG_INHERIT = 0x0001
DUPLICATE_CLOSE_SOURCE = 0x00000001
DUPLICATE_SAME_ACCESS = 0x00000002
INFINITE = 0xFFFFFFFF
WAIT_OBJECT_0 = 0
WAIT_TIMEOUT = 0x102
WAIT_FAILED = 0xFFFFFFFF
WAIT_ABANDONED = 0x80
STARTF_USESTDHANDLES = 0x0100
CREATE_NO_WINDOW = 0x08000000
STARTF_USESHOWWINDOW = 0x00000001
SW_HIDE = 0

CREATE_SUSPENDED = 0x00000004
CREATE_BREAKAWAY_FROM_JOB = 0x01000000

CREATE_NEW_CONSOLE = 0x00000010
NORMAL_PRIORITY_CLASS = 0x00000020
IDLE_PRIORITY_CLASS = 0x00000040
HIGH_PRIORITY_CLASS = 0x00000080

STD_INPUT_HANDLE = -10
STD_OUTPUT_HANDLE = -11
STD_ERROR_HANDLE = -12

JOB_OBJECT_MSG_END_OF_JOB_TIME = 1
JOB_OBJECT_MSG_END_OF_PROCESS_TIME = 2
JOB_OBJECT_MSG_ACTIVE_PROCESS_LIMIT = 3
JOB_OBJECT_MSG_ACTIVE_PROCESS_ZERO = 4
JOB_OBJECT_MSG_NEW_PROCESS = 6
JOB_OBJECT_MSG_EXIT_PROCESS = 7
JOB_OBJECT_MSG_ABNORMAL_EXIT_PROCESS = 8
JOB_OBJECT_MSG_PROCESS_MEMORY_LIMIT = 9
JOB_OBJECT_MSG_JOB_MEMORY_LIMIT = 10

JOB_OBJECT_LIMIT_WORKINGSET = 0x00000001
JOB_OBJECT_LIMIT_PROCESS_TIME = 0x00000002
JOB_OBJECT_LIMIT_JOB_TIME = 0x00000004
JOB_OBJECT_LIMIT_ACTIVE_PROCESS = 0x00000008
JOB_OBJECT_LIMIT_AFFINITY = 0x00000010
JOB_OBJECT_LIMIT_PRIORITY_CLASS = 0x00000020
JOB_OBJECT_LIMIT_PRESERVE_JOB_TIME = 0x00000040
JOB_OBJECT_LIMIT_SCHEDULING_CLASS = 0x00000080

JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
JOB_OBJECT_LIMIT_JOB_MEMORY = 0x00000200
JOB_OBJECT_LIMIT_DIE_ON_UNHANDLED_EXCEPTION = 0x00000400
JOB_OBJECT_LIMIT_BREAKAWAY_OK = 0x00000800
JOB_OBJECT_LIMIT_SILENT_BREAKAWAY_OK = 0x00001000
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000

JOB_OBJECT_LIMIT_SUBSET_AFFINITY = 0x00004000
JOB_OBJECT_LIMIT_RESERVED3 = 0x00008000
JOB_OBJECT_LIMIT_RESERVED4 = 0x00010000
JOB_OBJECT_LIMIT_RESERVED5 = 0x00020000
JOB_OBJECT_LIMIT_RESERVED6 = 0x00040000

JOB_OBJECT_LIMIT_VALID_FLAGS = 0x0007ffff

JOB_OBJECT_BASIC_LIMIT_VALID_FLAGS = 0x000000ff
JOB_OBJECT_EXTENDED_LIMIT_VALID_FLAGS = 0x00007fff
JOB_OBJECT_RESERVED_LIMIT_VALID_FLAGS = 0x0007ffff

JobObjectBasicAccountingInformation = 1
JobObjectBasicLimitInformation = 2
JobObjectBasicProcessIdList = 3
JobObjectBasicUIRestrictions = 4
JobObjectSecurityLimitInformation = 5
JobObjectEndOfJobTimeInformation = 6
JobObjectAssociateCompletionPortInformation = 7
JobObjectBasicAndIoAccountingInformation = 8
JobObjectExtendedLimitInformation = 9
JobObjectJobSetInformation = 10
JobObjectGroupInformation = 11
MaxJobObjectInfoClass = 12


class IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ('ReadOperationCount', c_uint64),
        ('WriteOperationCount', c_uint64),
        ('OtherOperationCount', c_uint64),
        ('ReadTransferCount', c_uint64),
        ('WriteTransferCount', c_uint64),
        ('OtherTransferCount', c_uint64),
    ]


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ('PerProcessUserTimeLimit', c_int64),
        ('PerJobUserTimeLimit', c_int64),
        ('LimitFlags', DWORD),
        ('MinimumWorkingSetSize', c_size_t),
        ('MaximumWorkingSetSize', c_size_t),
        ('ActiveProcessLimit', DWORD),
        ('Affinity', c_void_p),
        ('PriorityClass', DWORD),
        ('SchedulingClass', DWORD),
    ]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ('BasicLimitInformation', JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ('IoInfo', IO_COUNTERS),
        ('ProcessMemoryLimit', c_size_t),
        ('JobMemoryLimit', c_size_t),
        ('PeakProcessMemoryUsed', c_size_t),
        ('PeakJobMemoryUsed', c_size_t),
    ]


class JOBOBJECT_ASSOCIATE_COMPLETION_PORT(Structure):
    _fields_ = [('CompletionKey', c_ulong),
                ('CompletionPort', HANDLE)]


class SECURITY_ATTRIBUTES(Structure):
    _fields_ = [("Length", DWORD),
                ("SecDescriptor", LPVOID),
                ("InheritHandle", BOOL)]


class STARTUPINFO(ctypes.Structure):
    _fields_ = [
        ('cb', DWORD),
        ('lpReserved', c_void_p),
        ('lpDesktop', LPWSTR),
        ('lpTitle', LPWSTR),
        ('dwX', DWORD),
        ('dwY', DWORD),
        ('dwXSize', DWORD),
        ('dwYSize', DWORD),
        ('dwXCountChars', DWORD),
        ('dwYCountChars', DWORD),
        ('dwFillAttribute', DWORD),
        ('dwFlags', DWORD),
        ('wShowWindow', WORD),
        ('cbReserved2', WORD),
        ('lpReserved2', c_void_p),
        ('hStdInput', HANDLE),
        ('hStdOutput', HANDLE),
        ('hStdError', HANDLE),
    ]


class PROCESS_INFORMATION(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('hProcess', HANDLE),
        ('hThread', HANDLE),
        ('dwProcessId', DWORD),
        ('dwThreadId', DWORD),
    ]


class OVERLAPPED(ctypes.Structure):
    _fields_ = [
        ('Internal', c_void_p),
        ('InternalHigh', c_void_p),
        ('Offset', DWORD),
        ('OffsetHigh', DWORD),
        ('hEvent', HANDLE)
    ]


GetQueuedCompletionStatus = _kernel32.GetQueuedCompletionStatus
GetQueuedCompletionStatus.restype = BOOL
GetQueuedCompletionStatus.argtypes = (HANDLE, LPVOID, LPVOID, POINTER(OVERLAPPED), DWORD)
