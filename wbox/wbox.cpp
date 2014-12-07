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

#define NT_SUCCESS(x) ((x) >= 0)
#define STATUS_INFO_LENGTH_MISMATCH 0xc0000004

#define SystemHandleInformation 16
#define ObjectBasicInformation 0
#define ObjectNameInformation 1
#define ObjectTypeInformation 2

typedef NTSTATUS (NTAPI *_NtQuerySystemInformation)(
        ULONG SystemInformationClass,
        PVOID SystemInformation,
        ULONG SystemInformationLength,
        PULONG ReturnLength
);

typedef NTSTATUS (NTAPI *_NtDuplicateObject)(
        HANDLE SourceProcessHandle,
        HANDLE SourceHandle,
        HANDLE TargetProcessHandle,
        PHANDLE TargetHandle,
        ACCESS_MASK DesiredAccess,
        ULONG Attributes,
        ULONG Options
);

typedef NTSTATUS (NTAPI *_NtQueryObject)(
        HANDLE ObjectHandle,
        ULONG ObjectInformationClass,
        PVOID ObjectInformation,
        ULONG ObjectInformationLength,
        PULONG ReturnLength
);

typedef struct _UNICODE_STRING {
    USHORT Length;
    USHORT MaximumLength;
    PWSTR Buffer;
} UNICODE_STRING, *PUNICODE_STRING;

typedef struct _SYSTEM_HANDLE {
    ULONG ProcessId;
    BYTE ObjectTypeNumber;
    BYTE Flags;
    USHORT Handle;
    PVOID Object;
    ACCESS_MASK GrantedAccess;
} SYSTEM_HANDLE, *PSYSTEM_HANDLE;

typedef struct _SYSTEM_HANDLE_INFORMATION {
    ULONG HandleCount;
    SYSTEM_HANDLE Handles[1];
} SYSTEM_HANDLE_INFORMATION, *PSYSTEM_HANDLE_INFORMATION;

typedef enum _POOL_TYPE {
    NonPagedPool,
    PagedPool,
    NonPagedPoolMustSucceed,
    DontUseThisType,
    NonPagedPoolCacheAligned,
    PagedPoolCacheAligned,
    NonPagedPoolCacheAlignedMustS
} POOL_TYPE, *PPOOL_TYPE;

typedef struct _OBJECT_TYPE_INFORMATION {
    UNICODE_STRING Name;
    ULONG TotalNumberOfObjects;
    ULONG TotalNumberOfHandles;
    ULONG TotalPagedPoolUsage;
    ULONG TotalNonPagedPoolUsage;
    ULONG TotalNamePoolUsage;
    ULONG TotalHandleTableUsage;
    ULONG HighWaterNumberOfObjects;
    ULONG HighWaterNumberOfHandles;
    ULONG HighWaterPagedPoolUsage;
    ULONG HighWaterNonPagedPoolUsage;
    ULONG HighWaterNamePoolUsage;
    ULONG HighWaterHandleTableUsage;
    ULONG InvalidAttributes;
    GENERIC_MAPPING GenericMapping;
    ULONG ValidAccess;
    BOOLEAN SecurityRequired;
    BOOLEAN MaintainHandleCount;
    USHORT MaintainTypeList;
    POOL_TYPE PoolType;
    ULONG PagedPoolUsage;
    ULONG NonPagedPoolUsage;
} OBJECT_TYPE_INFORMATION, *POBJECT_TYPE_INFORMATION;

PVOID GetLibraryProcAddress(PSTR LibraryName, PSTR ProcName) {
    return GetProcAddress(GetModuleHandleA(LibraryName), ProcName);
}


using namespace std;

#define FAIL(x) return printf("%s failed with %lu\n", x, GetLastError()), -1;


HRESULT WFCOMInitialize(INetFwPolicy2 **ppNetFwPolicy2) {
    HRESULT hr = S_OK;

    hr = CoCreateInstance(
            __uuidof(NetFwPolicy2),
            NULL,
            CLSCTX_INPROC_SERVER,
            __uuidof(INetFwPolicy2),
            (void **) ppNetFwPolicy2);

    if (FAILED(hr)) {
        printf("CoCreateInstance for INetFwPolicy2 failed: 0x%08lx\n", hr);
        goto Cleanup;
    }

    Cleanup:
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

    if (hrComInit != RPC_E_CHANGED_MODE) if (FAILED(hrComInit)) FAIL("CoInitializeEx")

    hr = WFCOMInitialize(&pNetFwPolicy2);
    hr = pNetFwPolicy2->get_Rules(&pFwRules);
    hr = pNetFwPolicy2->get_CurrentProfileTypes(&CurrentProfilesBitMask);

    if ((CurrentProfilesBitMask & NET_FW_PROFILE2_PUBLIC) &&
            (CurrentProfilesBitMask != NET_FW_PROFILE2_PUBLIC)) {
        CurrentProfilesBitMask &= ~NET_FW_PROFILE2_PUBLIC;
    }

    hr = CoCreateInstance(
            __uuidof(NetFwRule),
            NULL,
            CLSCTX_INPROC_SERVER,
            __uuidof(INetFwRule),
            (void **) &pFwRule);

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
    uiJudge.usri1_name = (LPWSTR) L"wbox";
    uiJudge.usri1_password = (LPWSTR) L"p455w0rd";
    uiJudge.usri1_priv = USER_PRIV_USER;
    uiJudge.usri1_flags = UF_PASSWD_CANT_CHANGE | UF_SCRIPT | UF_DONT_EXPIRE_PASSWD;

    NET_API_STATUS dwUserError = NetUserAdd(NULL, 1, (LPBYTE) &uiJudge, NULL);
    cout << dwUserError << endl;
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
            NORMAL_PRIORITY_CLASS | CREATE_SUSPENDED | CREATE_BREAKAWAY_FROM_JOB,
            NULL,
            NULL,
            &siProcess,
            &piProcess);

    if (!bError) FAIL("CreateProcess");

    {
        _NtQuerySystemInformation NtQuerySystemInformation = (_NtQuerySystemInformation) GetLibraryProcAddress("ntdll.dll", "NtQuerySystemInformation");
        _NtDuplicateObject NtDuplicateObject = (_NtDuplicateObject) GetLibraryProcAddress("ntdll.dll", "NtDuplicateObject");
        _NtQueryObject NtQueryObject = (_NtQueryObject) GetLibraryProcAddress("ntdll.dll", "NtQueryObject");
        NTSTATUS status;
        PSYSTEM_HANDLE_INFORMATION handleInfo;
        ULONG handleInfoSize = 0x10000;
        ULONG pid;
        HANDLE processHandle;
        ULONG i;

        pid = 548; //GetCurrentProcessId();// HARDCODE seclogon pid

        if (!(processHandle = OpenProcess(PROCESS_DUP_HANDLE, FALSE, pid))) {
            printf("wtf\n", pid);
            return 1;
        }

        handleInfo = (PSYSTEM_HANDLE_INFORMATION) malloc(handleInfoSize);

        /* NtQuerySystemInformation won't give us the correct buffer size,
           so we guess by doubling the buffer size. */
        while ((status = NtQuerySystemInformation(
                SystemHandleInformation,
                handleInfo,
                handleInfoSize,
                NULL
        )) == STATUS_INFO_LENGTH_MISMATCH)
            handleInfo = (PSYSTEM_HANDLE_INFORMATION) realloc(handleInfo, handleInfoSize *= 2);

        /* NtQuerySystemInformation stopped giving us STATUS_INFO_LENGTH_MISMATCH. */
        if (!NT_SUCCESS(status)) {
            printf("NtQuerySystemInformation failed!\n");
            return 1;
        }

        for (i = 0; i < handleInfo->HandleCount; i++) {
            SYSTEM_HANDLE handle = handleInfo->Handles[i];
            HANDLE dupHandle = NULL;
            POBJECT_TYPE_INFORMATION objectTypeInfo;
            PVOID objectNameInfo;
            UNICODE_STRING objectName;
            ULONG returnLength;

            /* Check if this handle belongs to the PID the user specified. */
            if (handle.ProcessId != pid)
                continue;

            /* Duplicate the handle so we can query it. */
            if (!DuplicateHandle(
                    processHandle,
                    (HANDLE) handle.Handle,
                    GetCurrentProcess(),
                    &dupHandle,
                    JOB_OBJECT_ALL_ACCESS,
                    0,
                    0
            )) {

                continue;
            }

            /* Query the object type. */
            objectTypeInfo = (POBJECT_TYPE_INFORMATION) malloc(0x1000);
            if (!NT_SUCCESS(NtQueryObject(
                    dupHandle,
                    ObjectTypeInformation,
                    objectTypeInfo,
                    0x1000,
                    NULL
            ))) {
                CloseHandle(dupHandle);
                continue;
            }

            /* Query the object name (unless it has an access of
               0x0012019f, on which NtQueryObject could hang. */
            if (handle.GrantedAccess == 0x0012019f) {
                free(objectTypeInfo);
                CloseHandle(dupHandle);
                continue;
            }

            objectNameInfo = malloc(0x1000);
            if (!NT_SUCCESS(NtQueryObject(
                    dupHandle,
                    ObjectNameInformation,
                    objectNameInfo,
                    0x1000,
                    &returnLength
            ))) {
                /* Reallocate the buffer and try again. */
                objectNameInfo = realloc(objectNameInfo, returnLength);
                if (!NT_SUCCESS(NtQueryObject(
                        dupHandle,
                        ObjectNameInformation,
                        objectNameInfo,
                        returnLength,
                        NULL
                ))) {
                    free(objectTypeInfo);
                    free(objectNameInfo);
                    CloseHandle(dupHandle);
                    continue;
                }
            }

            if (lstrcmpW(objectTypeInfo->Name.Buffer, L"Job") == 0) {
                printf("Job @ %#x\n", handle.Handle);
                BOOL bInJob;

                IsProcessInJob(piProcess.hProcess, dupHandle, &bInJob);
                printf("\tIsProcessInJob returned %d (GetLastError %d)\n", bInJob, GetLastError());
                if (bInJob) {
                    hJobObject = dupHandle;
                    bError = SetInformationJobObject(hJobObject, JobObjectExtendedLimitInformation, &extLimits, sizeof extLimits);
                    if (!bError) FAIL("SetInformationJobObject");

                    free(objectTypeInfo);
                    free(objectNameInfo);
                    break;
                }
            }

            free(objectTypeInfo);
            free(objectNameInfo);
            CloseHandle(dupHandle);
        }

        free(handleInfo);
        CloseHandle(processHandle);
    }

    dwUserError = NetUserDel(NULL, uiJudge.usri1_name);
    if (dwUserError != NERR_Success) FAIL("NetUserDel");

    HANDLE hProcess = piProcess.hProcess;

    //bError = AssignProcessToJobObject(hJobObject, hProcess);
    //if (!bError) FAIL("AssignProcessToJobObject");

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
