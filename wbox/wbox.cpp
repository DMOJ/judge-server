#define WINVER 0x0502
#define WIN32_LEAN_AND_MEAN

#ifndef UNICODE
#define UNICODE
#endif // UNICODE

#include <windows.h>
#include <lmcons.h>
#include <lmaccess.h>
#include <lmerr.h>
#include <lmapibuf.h>
#include <stdio.h>
#include <stdlib.h>

#include <windows.h>
#include <netfw.h>
#include <objbase.h>
#include <oleauto.h>
#include <stdio.h>

#include <iostream>
#include <windows.h>
#include <windowsx.h>
#include <psapi.h>
#include <tchar.h>
#include <stdio.h>

#pragma comment(lib, "netapi32.lib")
#pragma comment(lib, "ole32.lib")
#pragma comment(lib, "oleaut32.lib")

#include <lm.h>
#include <lmaccess.h>
#include <daogetrw.h>

using namespace std;

#define FAIL(x) return printf("%s failed with %lu\n", x, GetLastError()), -1;

HRESULT WFCOMInitialize(INetFwPolicy2** ppNetFwPolicy2)
{
    HRESULT hr = S_OK;

    hr = CoCreateInstance(
        __uuidof(NetFwPolicy2),
        NULL,
        CLSCTX_INPROC_SERVER,
        __uuidof(INetFwPolicy2),
        (void**)ppNetFwPolicy2);

    if (FAILED(hr))
    {
        printf("CoCreateInstance for INetFwPolicy2 failed: 0x%08lx\n", hr);
        goto error;
    }

error:
    return hr;
}

int main() {
	HRESULT hrComInit = S_OK;
    HRESULT hr = S_OK;

    INetFwPolicy2 *pNetFwPolicy2 = NULL;
    INetFwRules *pFwRules = NULL;
    INetFwRule *pFwRule = NULL;

    long CurrentProfilesBitMask = 0;

    BSTR bstrRuleName = SysAllocString(L"DMOJ Submission Network Block");
    BSTR bstrRuleDescription = SysAllocString(L"Block DMOJ submissions from accessing the network");
    BSTR bstrRuleGroup = SysAllocString(L"DMOJ");
    BSTR bstrRuleApplication = SysAllocString(L"C:\\Python27\\python.exe");
    BSTR bstrRuleLPorts = SysAllocString(L"all");

    hrComInit = CoInitializeEx(
                    0,
                    COINIT_APARTMENTTHREADED
                    );

    if (hrComInit != RPC_E_CHANGED_MODE)
        if (FAILED(hrComInit)) FAIL("CoInitializeEx")

    hr = WFCOMInitialize(&pNetFwPolicy2);
    hr = pNetFwPolicy2->get_Rules(&pFwRules);
    hr = pNetFwPolicy2->get_CurrentProfileTypes(&CurrentProfilesBitMask);

    if ((CurrentProfilesBitMask & NET_FW_PROFILE2_PUBLIC) &&
        (CurrentProfilesBitMask != NET_FW_PROFILE2_PUBLIC))
    {
        CurrentProfilesBitMask &= ~NET_FW_PROFILE2_PUBLIC;
    }

    hr = CoCreateInstance(
                __uuidof(NetFwRule),
                NULL,
                CLSCTX_INPROC_SERVER,
                __uuidof(INetFwRule),
                (void**)&pFwRule);

    pFwRule->put_Name(bstrRuleName);
    pFwRule->put_Description(bstrRuleDescription);
    pFwRule->put_ApplicationName(bstrRuleApplication);
    pFwRule->put_Protocol(NET_FW_IP_PROTOCOL_TCP);
    pFwRule->put_LocalPorts(bstrRuleLPorts);
    pFwRule->put_Direction(NET_FW_RULE_DIR_OUT);
    pFwRule->put_Grouping(bstrRuleGroup);
    pFwRule->put_Profiles(CurrentProfilesBitMask);
    pFwRule->put_Action(NET_FW_ACTION_BLOCK);
    pFwRule->put_Enabled(VARIANT_TRUE);

    hr = pFwRules->Add(pFwRule);

    BOOL bError;
    DWORD milliseconds = 3000;
    size_t mxWorkingSetSize = 65536 * 1024;

    LARGE_INTEGER ticks;
    ticks.QuadPart = milliseconds * 1000000 / 100;

    JOBOBJECT_EXTENDED_LIMIT_INFORMATION extLimits;
    ZeroMemory(&extLimits, sizeof extLimits);
    extLimits.JobMemoryLimit = mxWorkingSetSize;
    extLimits.BasicLimitInformation.PerJobUserTimeLimit = ticks;
    extLimits.BasicLimitInformation.LimitFlags =
            JOB_OBJECT_LIMIT_ACTIVE_PROCESS |
                    JOB_OBJECT_LIMIT_JOB_MEMORY |
                    JOB_OBJECT_LIMIT_JOB_TIME;
    extLimits.BasicLimitInformation.ActiveProcessLimit = 1;
    extLimits.BasicLimitInformation.PriorityClass = NORMAL_PRIORITY_CLASS;

    HANDLE hJobObject;
    hJobObject = CreateJobObject(NULL, NULL);

    bError = SetInformationJobObject(hJobObject, JobObjectExtendedLimitInformation, &extLimits, sizeof extLimits);
    if (!bError) FAIL("SetInformationJobObject");

    STARTUPINFO siProcess;
    ZeroMemory(&siProcess, sizeof siProcess);
    siProcess.cb = sizeof siProcess;

    siProcess.hStdError = GetStdHandle(STD_ERROR_HANDLE);
    siProcess.hStdOutput = GetStdHandle(STD_OUTPUT_HANDLE);
    siProcess.hStdInput = NULL;
    siProcess.dwFlags |= STARTF_USESTDHANDLES;

    PROCESS_INFORMATION piProcess;
    ZeroMemory(&piProcess, sizeof piProcess);

    USER_INFO_1 uiJudge;
    ZeroMemory(&uiJudge, sizeof uiJudge);
    uiJudge.usri1_name = (LPWSTR) L"judge_user";
    uiJudge.usri1_password = (LPWSTR) L"p455w0rd";
    uiJudge.usri1_priv = USER_PRIV_USER;
    uiJudge.usri1_flags = UF_PASSWD_CANT_CHANGE | UF_SCRIPT | UF_DONT_EXPIRE_PASSWD;

    NET_API_STATUS dwUserError = NetUserAdd(NULL, 1, (LPBYTE) &uiJudge, NULL);
    if (dwUserError != NERR_Success) FAIL("NetUserAdd");

    WCHAR wcCmdline[256] = L"C:\\Python27\\python.exe \"C:\\test.py\"";

	int a = TOKEN_QUERY;

    bError = CreateProcessWithLogonW(
            uiJudge.usri1_name,
            L"localhost",
            uiJudge.usri1_password,
            0,
            NULL,
            wcCmdline,
            NORMAL_PRIORITY_CLASS | CREATE_SUSPENDED | CREATE_BREAKAWAY_FROM_JOB ,
            NULL,
            NULL,
            &siProcess,
            &piProcess);

    if (!bError) FAIL("CreateProcess");

    dwUserError = NetUserDel(NULL, uiJudge.usri1_name);
    if (dwUserError != NERR_Success) FAIL("NetUserDel");

    HANDLE hProcess = piProcess.hProcess;

    bError = AssignProcessToJobObject(hJobObject, hProcess);
    if (!bError) FAIL("AssignProcessToJobObject");

    ResumeThread(piProcess.hThread);
    bError = CloseHandle(piProcess.hThread);
    if (!bError) FAIL("CloseHandle(process thread)");

    DWORD dwWait = WaitForSingleObject(piProcess.hProcess, milliseconds);
    BOOL bTle = dwWait != WAIT_OBJECT_0;
    if (bTle)
        TerminateProcess(piProcess.hProcess, 0xdeadbeef);
    WaitForSingleObject(piProcess.hProcess, INFINITE);
    DWORD dwErr;
    GetExitCodeProcess(piProcess.hProcess, &dwErr);
    CloseHandle(piProcess.hProcess);

    bError = QueryInformationJobObject(hJobObject, JobObjectExtendedLimitInformation, &extLimits, sizeof extLimits, NULL);
    if (!bError) FAIL("QueryInformationJobObject");

    printf("---\n");
    printf("Exit code: %lu\n", dwErr);
    printf("TLE: %d\n", bTle);
    printf("Peak mem: %.2fmb (%lu bytes)\n", extLimits.PeakJobMemoryUsed / 1024.0 / 1024, extLimits.PeakJobMemoryUsed);

    hr = pFwRules->Remove(bstrRuleName);

    return 0;
}
