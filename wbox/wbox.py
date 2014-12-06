import subprocess

from wbox.bindings import *


__author__ = 'Tudor'


def run_wbox(cmdline, time_limit_ms, memory_limit_kb):
    # Time limit in 100ns ticks
    time_limit_ticks = LARGE_INTEGER(time_limit_ms * 1000000 / 100)
    working_set_size = memory_limit_kb

    limits = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    limits.JobMemoryLimit = working_set_size
    limits.BasicLimitInformation.PerJobUserTimeLimit = time_limit_ticks
    limits.BasicLimitInformation.LimitFlags = \
        JOB_OBJECT_LIMIT_ACTIVE_PROCESS | JOB_OBJECT_LIMIT_JOB_MEMORY | JOB_OBJECT_LIMIT_JOB_TIME
    limits.BasicLimitInformation.ActiveProcessLimit = 1
    limits.BasicLimitInformation.PriorityClass = NORMAL_PRIORITY_CLASS

    job = kernel32.CreateJobObjectA(None, None)
    if not job:
        raise AssertionError('CreateJobObjectA %d' % GetLastError())

    if not kernel32.SetInformationJobObject(job,
                                            JobObjectExtendedLimitInformation,
                                            byref(limits),
                                            sizeof(JOBOBJECT_EXTENDED_LIMIT_INFORMATION)):
        raise AssertionError('SetInformationJobObject %d' % GetLastError())

    siProcess = STARTUPINFO()
    siProcess.cb = sizeof(STARTUPINFO)
    siProcess.dwFlags = STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW
    siProcess.hStdInput = kernel32.GetStdHandle(STD_INPUT_HANDLE)
    siProcess.hStdOutput = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    siProcess.hStdError = kernel32.GetStdHandle(STD_ERROR_HANDLE)
    siProcess.wShowWindow = SW_HIDE

    uiJudge = USER_INFO_1()
    uiJudge.usri1_name = c_wchar_p("judge_user")
    uiJudge.usri1_password = c_wchar_p("p455w0rd")
    uiJudge.usri1_priv = 1  # USER_PRIV_USER
    uiJudge.usri1_flags = UF_PASSWD_CANT_CHANGE | UF_SCRIPT | UF_DONT_EXPIRE_PASSWD

    net_err = netapi32.NetUserAdd(NULL, 1, byref(uiJudge), NULL)
    if net_err:
        raise AssertionError('NetUserAdd %d' % net_err)

    piProcess = PROCESS_INFORMATION()
    piProcess.hProcess = INVALID_HANDLE_VALUE
    piProcess.hThread = INVALID_HANDLE_VALUE
    piProcess.dwProcessId = 0
    piProcess.dwThreadId = 0

    if not advapi32.CreateProcessWithLogonW(uiJudge.usri1_name,
                                            c_wchar_p('localhost'),
                                            uiJudge.usri1_password,
                                            0,
                                            NULL,
                                            create_unicode_buffer(subprocess.list2cmdline(cmdline)),
                                            NORMAL_PRIORITY_CLASS | CREATE_SUSPENDED | CREATE_BREAKAWAY_FROM_JOB,
                                            NULL,
                                            NULL,
                                            byref(siProcess),
                                            byref(piProcess)):
        raise AssertionError('CreateProcess %d' % GetLastError())

    net_err = netapi32.NetUserDel(NULL, uiJudge.usri1_name)
    if net_err:
        raise AssertionError('NetUserDel %d' % net_err)

    if kernel32.AssignProcessToJobObject(job, piProcess.hProcess) == 0:
        raise AssertionError('AssignProcessToJobObject %d' % GetLastError())

    if kernel32.ResumeThread(piProcess.hThread) == -1:
        raise AssertionError('ResumeThread %d' % GetLastError())

    if kernel32.CloseHandle(piProcess.hThread) == 0:
        raise AssertionError('CloseHandle(process thread) %d' % GetLastError())

    wait = kernel32.WaitForSingleObject(piProcess.hProcess, time_limit_ms)
    tle = bool(wait)
    if tle:
        kernel32.TerminateProcess(piProcess.hProcess, 0xdeadbeef)
        print 'Process is deadbeef'
    kernel32.WaitForSingleObject(piProcess.hProcess, INFINITE)

    if kernel32.QueryInformationJobObject(job,
                                          JobObjectExtendedLimitInformation,
                                          byref(limits),
                                          sizeof(JOBOBJECT_EXTENDED_LIMIT_INFORMATION),
                                          NULL) == 0:
        raise AssertionError('QueryInformationJobObject %d' % GetLastError())

    err = DWORD()
    kernel32.GetExitCodeProcess(piProcess.hProcess, byref(err))
    print "Process exited with", err.value

    print "Peak mem: %.2fmb (%lu bytes)\n" % (limits.PeakJobMemoryUsed / 1024.0 / 1024, limits.PeakJobMemoryUsed)


test = '''
import urllib2
import os
import getpass

print "Starting on user %s..." % getpass.getuser()

def test(name, func, err):
    print "Testing %s..." % name
    try:
        func()
        print "\tFailed"
    except:
        print "\tSuccess, blocked"


def fopen():
    open(r"C:\file.txt", 'w')


def network():
    urllib2.urlopen('http://dmoj.ca').read()


test('network access', network, 500)
test('file access', fopen, 100)
'''

run_wbox([r'C:\Python27\python.exe', '-c', test], 5000, 65536 * 1024)