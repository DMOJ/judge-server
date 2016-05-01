#include "process.h"
#include "handles.h"
#include <objbase.h>
#include <strsafe.h>

bool JobbedProcessManager::canX86 = false;
bool JobbedProcessManager::canX64 = false; 
JobbedProcessManager::_init JobbedProcessManager::_initializer;

BYTE JobbedProcessManager::asmX86[] = {
    /* 0000 */ 0x55,             // push        ebp
    /* 0001 */ 0x8B, 0xEC,       // mov         ebp, esp
    /* 0003 */ 0x68, 0, 0, 0, 0, // push        <library name (UTF-16)>
    /* 0008 */ 0xB9, 0, 0, 0, 0, // mov         ecx, LoadLibraryW
    /* 000D */ 0xFF, 0xD1,       // call        ecx
    /* 000F */ 0x68, 0, 0, 0, 0, // push        <function name (ASCII)>
    /* 0014 */ 0x50,             // push        eax
    /* 0015 */ 0xB9, 0, 0, 0, 0, // mov         ecx, GetProcAddress
    /* 001A */ 0xFF, 0xD1,       // call        ecx
    /* 001C */ 0xFF, 0xD0,       // call        eax
    /* 001E */ 0x33, 0xC0,       // xor         eax, eax
    /* 0020 */ 0x5D,             // pop         ebp
    /* 0021 */ 0xC2, 0x04, 0     // ret         4
};

BYTE JobbedProcessManager::asmX64[] = {
    /* 0000 */ 0x48, 0x89, 0x4C, 0x24, 0x08,       // mov  qword ptr [rsp+8], rcx
    /* 0005 */ 0x48, 0x83, 0xEC, 0x28,             // sub  rsp, 28h
    /* 0009 */ 0x48, 0xB9, 0, 0, 0, 0, 0, 0, 0, 0, // mov  rcx, <library name (UTF-16)>
    /* 0013 */ 0x49, 0xBA, 0, 0, 0, 0, 0, 0, 0, 0, // mov  r10, LoadLibraryW
    /* 001D */ 0x41, 0xFF, 0xD2,                   // call r10
    /* 0020 */ 0x48, 0xBA, 0, 0, 0, 0, 0, 0, 0, 0, // mov  rdx, <function name (ASCII)>
    /* 002A */ 0x48, 0x8B, 0xC8,                   // mov  rcx, rax
    /* 002D */ 0x49, 0xBA, 0, 0, 0, 0, 0, 0, 0, 0, // mov  r10, GetProcAddress
    /* 0037 */ 0x41, 0xFF, 0xD2,                   // call r10
    /* 003A */ 0xFF, 0xD0,                         // call rax
    /* 003C */ 0x33, 0xC0,                         // xor  eax, eax
    /* 003E */ 0x48, 0x83, 0xC4, 0x28,             // add  rsp, 28h
    /* 0042 */ 0xC3,                               // ret
};

bool LaunchProcessUpdateSharedMemory(LPCWSTR lpExecutable, LPVOID lpvMemory, DWORD dwLength)
{
    SECURITY_ATTRIBUTES sa;
    HANDLE hMapping;
    WCHAR szBuffer[50];
    bool bSuccess = true;
    STARTUPINFOW si = { sizeof(si) };
    PROCESS_INFORMATION pi;
    DWORD dwExitCode;
    
    sa.nLength = sizeof sa;
    sa.lpSecurityDescriptor = NULL;
    sa.bInheritHandle = TRUE;
    
    hMapping = CreateFileMapping(INVALID_HANDLE_VALUE, &sa, PAGE_READWRITE, 0, dwLength, NULL);
    if (hMapping) {
        LPVOID lpMapping = MapViewOfFile(hMapping, FILE_MAP_WRITE, 0, 0, 0);
        
        if (lpMapping) {
            StringCchPrintfW(szBuffer, 50, L"%I64d", (INT64) (INT_PTR) hMapping);
            
            if (CreateProcessW(lpExecutable, szBuffer, NULL, NULL, TRUE, 0, NULL, NULL, &si, &pi)) {
                WaitForSingleObject(pi.hProcess, INFINITE);
                if (GetExitCodeProcess(pi.hProcess, &dwExitCode)) {
                    bSuccess = !dwExitCode;
                } else bSuccess = false;

                CloseHandle(pi.hProcess);
                CloseHandle(pi.hThread);
                memcpy(lpvMemory, lpMapping, dwLength);
            } else bSuccess = false;
            
            UnmapViewOfFile(lpMapping);
        } else bSuccess = false;
        
        CloseHandle(hMapping);
    } else bSuccess = false;
    return bSuccess;
}

bool JobbedProcessManager::inject(HANDLE hProcess, BOOL x64, LPCWSTR szDllPath, LPCSTR szFunctionName)
{
    HANDLE hInject;
    BYTE asmCode[sizeof asmX64];
    LPVOID lpDllPath, lpFunctionName, lpCode;
    DWORD cbDllPath, cbFunctionName = lstrlenA(szFunctionName) + 1;

    cbDllPath = (lstrlenW(szDllPath) + 1) * sizeof(WCHAR);
    
    lpDllPath = VirtualAllocEx(hProcess, NULL, cbDllPath, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    if (!lpDllPath)
        return false;

    if (!WriteProcessMemory(hProcess, lpDllPath, szDllPath, cbDllPath, NULL))
        return false;

    lpFunctionName = VirtualAllocEx(hProcess, NULL, cbFunctionName, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    if (!lpFunctionName)
        return false;

    if (!WriteProcessMemory(hProcess, lpFunctionName, szFunctionName, cbFunctionName, NULL))
        return false;

    if (x64) {
        DWORD64 qwDllPath, qwFunctionName;

        memcpy(asmCode, asmX64, sizeof asmX64);
        qwDllPath = (DWORD64) (INT_PTR) lpDllPath;
        qwFunctionName = (DWORD64) (INT_PTR) lpFunctionName;
        
        writeQword(asmCode + 11, qwDllPath);
        writeQword(asmCode + 34, qwFunctionName);
    } else {
        DWORD dwDllPath, dwFunctionName;

        memcpy(asmCode, asmX86, sizeof asmX86);
        dwDllPath = (DWORD) (INT_PTR) lpDllPath;
        dwFunctionName = (DWORD) (INT_PTR) lpFunctionName;

        writeDword(asmCode + 4, dwDllPath);
        writeDword(asmCode + 16, dwFunctionName);
    }

    lpCode = VirtualAllocEx(hProcess, NULL, sizeof asmCode, MEM_RESERVE | MEM_COMMIT, PAGE_EXECUTE_READWRITE);
    if (!lpCode)
        return false;

    if (!WriteProcessMemory(hProcess, lpCode, asmCode, sizeof asmCode, NULL))
        return false;

    if (!(hInject = CreateRemoteThread(hProcess, NULL, 0, (LPTHREAD_START_ROUTINE) lpCode, NULL, 0, NULL)))
        return false;
    
    WaitForSingleObject(hInject, INFINITE);

    VirtualFreeEx(hProcess, lpDllPath, cbDllPath, MEM_RELEASE);
    VirtualFreeEx(hProcess, lpFunctionName, cbFunctionName, MEM_RELEASE);
    VirtualFreeEx(hProcess, lpCode, sizeof asmCode, MEM_RELEASE);
    return true;
}

DWORD JobbedProcessManager::s_ShockerProc(LPVOID lpParam) {
	return static_cast<JobbedProcessManager*>(lpParam)->ShockerProc();
}
    
void JobbedProcessManager::updateAsmX86(LPCWSTR szExecutable)
{
    if (canX86) {
        INJECTION_PROCESS_X86 ipx86;

        if (LaunchProcessUpdateSharedMemory(szExecutable, &ipx86, sizeof ipx86)) {
            writeDword(asmX86 + 9, ipx86.u32LoadLibraryW);
            writeDword(asmX86 + 22, ipx86.u32GetProcAddress);
        } else canX86 = false;
    }
}

void JobbedProcessManager::updateAsmX64(LPCWSTR szExecutable)
{
    if (canX64) {
        INJECTION_PROCESS_X64 ipx64;

        if (LaunchProcessUpdateSharedMemory(szExecutable, &ipx64, sizeof ipx64)) {
            writeQword(asmX64 + 21, ipx64.u64LoadLibraryW);
            writeQword(asmX64 + 47, ipx64.u64GetProcAddress);
        } else canX64 = false;
    }
}

JobbedProcessManager::JobbedProcessManager() :
		szUsername(nullptr), szPassword(nullptr), szDirectory(nullptr), szCmdLine(nullptr),
		szExecutable(nullptr), szEnvBlock(nullptr), szInjectX86(nullptr),
        szInjectX64(nullptr), szInjectFunction(nullptr),
		tle_(false), mle_(false), terminate_shocker(false) {
	ZeroMemory(&extLimits, sizeof extLimits);
	extLimits.BasicLimitInformation.ActiveProcessLimit = 1;
	extLimits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_ACTIVE_PROCESS;
	ZeroMemory(&uiLimits, sizeof uiLimits);
	uiLimits.UIRestrictionsClass = 	JOB_OBJECT_UILIMIT_DESKTOP |
									JOB_OBJECT_UILIMIT_DISPLAYSETTINGS |
									JOB_OBJECT_UILIMIT_EXITWINDOWS |
									JOB_OBJECT_UILIMIT_GLOBALATOMS |
									JOB_OBJECT_UILIMIT_HANDLES |
									JOB_OBJECT_UILIMIT_READCLIPBOARD |
									JOB_OBJECT_UILIMIT_SYSTEMPARAMETERS |
									JOB_OBJECT_UILIMIT_WRITECLIPBOARD;
	CoCreateGuid(&guid);
	StringFromGUID2(guid, szGuid, ARRAYSIZE(szGuid));
}

bool JobbedProcessManager::spawn() {
	HANDLE handle;
	STARTUPINFO si = {sizeof(STARTUPINFO), 0};
	PROCESS_INFORMATION pi;
    bool x64;
    LPWSTR szDll;

	if (!szUsername)
		return false;

	if (!CreatePipe(&si.hStdInput, &handle, nullptr, 0))
		throw WindowsException("CreatePipe stdin");
	hStdin = handle;

	if (!CreatePipe(&handle, &si.hStdOutput, nullptr, 0))
		throw WindowsException("CreatePipe stdout");
	hStdout = handle;

	if (!CreatePipe(&handle, &si.hStdError, nullptr, 0))
		throw WindowsException("CreatePipe stderr");
	hStderr = handle;
	si.dwFlags |= STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW;
	si.wShowWindow = SW_HIDE;

	if (!CreateProcessWithLogonW(szUsername, L".", szPassword, 0, szExecutable, szCmdLine,
								 NORMAL_PRIORITY_CLASS | CREATE_SUSPENDED | CREATE_BREAKAWAY_FROM_JOB |
								 CREATE_UNICODE_ENVIRONMENT,
								 szEnvBlock, szDirectory, &si, &pi))
		throw WindowsException("CreateProcessWithLogonW");

	CloseHandle(si.hStdInput);
	CloseHandle(si.hStdOutput);
	CloseHandle(si.hStdError);
	hProcess = pi.hProcess;
    
#ifdef _WIN64
    BOOL wow64;
    IsWow64Process(hProcess, &wow64);
    x64 = !wow64;
#else
    x64 = false;
#endif
    szDll = x64 ? szInjectX64 : szInjectX86;

    if (szInjectFunction && szDll)
        if (!inject(hProcess, x64, x64 ? szInjectX64 : szInjectX86, szInjectFunction))
            throw WindowsException("Failed to inject DLL");

	if (!(handle = SearchForJobByService(hProcess, L"seclogon")))
		throw WindowsException("Failed to find job", 0);

	hJob = handle;
	if (!SetInformationJobObject(hJob, JobObjectExtendedLimitInformation, &extLimits, sizeof extLimits))
		throw WindowsException("SetInformationJobObject JobObjectExtendedLimitInformation");

	if (!SetInformationJobObject(hJob, JobObjectBasicUIRestrictions, &uiLimits, sizeof uiLimits))
		throw WindowsException("SetInformationJobObject JobObjectBasicUIRestrictions");

	LARGE_INTEGER liFreq;
	QueryPerformanceFrequency(&liFreq);
	qpc_freq = 1.0 / liFreq.QuadPart;
	QueryPerformanceCounter(&liStart);
	ResumeThread(pi.hThread);
	CloseHandle(pi.hThread);

	if (!(handle = CreateThread(nullptr, 0, s_ShockerProc, this, 0, nullptr)))
		throw WindowsException("CreateThread");
	hShocker = handle;

	return true;
}

bool JobbedProcessManager::terminate(unsigned code) {
	if (hProcess) {
		if (!TerminateProcess(hProcess, code))
			throw WindowsException("TerminateProcess");
    }
	return false;
}

JobbedProcessManager &JobbedProcessManager::time(double seconds) {
	if (seconds) {
		extLimits.BasicLimitInformation.PerJobUserTimeLimit.QuadPart = uint64_t(seconds * 1000 * 1000 * 10);
		extLimits.BasicLimitInformation.LimitFlags |= JOB_OBJECT_LIMIT_JOB_TIME;
		time_limit = seconds;
	} else {
		extLimits.BasicLimitInformation.LimitFlags &= ~JOB_OBJECT_LIMIT_JOB_TIME;
		time_limit = 0;
	}
	return *this;
}

JobbedProcessManager &JobbedProcessManager::memory(size_t bytes) {
	if (bytes) {
		extLimits.JobMemoryLimit = bytes;
		extLimits.BasicLimitInformation.LimitFlags |= JOB_OBJECT_LIMIT_JOB_MEMORY;
		memory_limit = bytes;
	} else {
		extLimits.BasicLimitInformation.LimitFlags &= ~JOB_OBJECT_LIMIT_JOB_MEMORY;
		memory_limit = 0;
	}
	return *this;
}

JobbedProcessManager &JobbedProcessManager::processes(int count) {
	if (count) {
		extLimits.BasicLimitInformation.ActiveProcessLimit = count;
		extLimits.BasicLimitInformation.LimitFlags |= JOB_OBJECT_LIMIT_ACTIVE_PROCESS;
	} else
		extLimits.BasicLimitInformation.LimitFlags &= ~JOB_OBJECT_LIMIT_ACTIVE_PROCESS;
	return *this;
}

inline void safe_alloc_and_copy_with_free(LPWSTR &dest, LPCWSTR source) {
	if (dest)
		free(dest);
	size_t bytes = (lstrlen(source) + 1) * sizeof(WCHAR);
	dest = (LPWSTR) malloc(bytes);
	StringCbCopy(dest, bytes, source);
}

inline void safe_alloc_and_copy_with_free(LPSTR &dest, LPCSTR source) {
	if (dest)
		free(dest);
	size_t bytes = lstrlenA(source) + 1;
	dest = (LPSTR) malloc(bytes);
	StringCbCopyA(dest, bytes, source);
}

JobbedProcessManager& JobbedProcessManager::withLogin(LPCWSTR szUsername, LPCWSTR szPassword) {
	safe_alloc_and_copy_with_free(this->szUsername, szUsername);
	safe_alloc_and_copy_with_free(this->szPassword, szPassword);
	return *this;
}

JobbedProcessManager& JobbedProcessManager::command(LPCWSTR szCmdLine) {
	safe_alloc_and_copy_with_free(this->szCmdLine, szCmdLine);
	return *this;
}

JobbedProcessManager& JobbedProcessManager::executable(LPCWSTR szExecutable) {
	safe_alloc_and_copy_with_free(this->szExecutable, szExecutable);
	return *this;
}

JobbedProcessManager& JobbedProcessManager::directory(LPCWSTR szDirectory) {
	safe_alloc_and_copy_with_free(this->szDirectory, szDirectory);
	return *this;
}

JobbedProcessManager& JobbedProcessManager::injectX86(LPCWSTR szExecutable) {
	safe_alloc_and_copy_with_free(this->szInjectX86, szExecutable);
	return *this;
}

JobbedProcessManager& JobbedProcessManager::injectX64(LPCWSTR szExecutable) {
	safe_alloc_and_copy_with_free(this->szInjectX64, szExecutable);
	return *this;
}

JobbedProcessManager& JobbedProcessManager::injectFunction(LPCSTR szFunction) {
	safe_alloc_and_copy_with_free(this->szInjectFunction, szFunction);
	return *this;
}

JobbedProcessManager& JobbedProcessManager::environment(LPCWSTR szEnvBlock, size_t cbBytes) {
	if (this->szEnvBlock)
		free(this->szEnvBlock);
	if (szEnvBlock && cbBytes) {
		this->szEnvBlock = (LPWSTR) malloc(cbBytes);
		memcpy(this->szEnvBlock, szEnvBlock, cbBytes);
	} else
		this->szEnvBlock = nullptr;
	return *this;
}

DWORD JobbedProcessManager::return_code() {
	DWORD out;
	if (!GetExitCodeProcess(hProcess, &out))
		throw WindowsException("GetExitCodeProcess");
	return out;
}

bool JobbedProcessManager::wait(DWORD time) {
	switch (WaitForSingleObject(hProcess, time)) {
	case WAIT_OBJECT_0:
        WaitForSingleObject(hShocker, INFINITE);
		return true;
	case WAIT_FAILED:
		throw WindowsException("WaitForSingleObject");
	default:
		return false;
	}
}

JobbedProcessManager::~JobbedProcessManager() {
	terminate_shocker = true;
	WaitForSingleObject(hShocker, INFINITE);
}

DWORD JobbedProcessManager::ShockerProc() {
	JOBOBJECT_EXTENDED_LIMIT_INFORMATION extLimit;
	LARGE_INTEGER qpc;
	DWORD result = WAIT_TIMEOUT;
	
	while (!terminate_shocker && result == WAIT_TIMEOUT) {
		result = WaitForSingleObject(hProcess, 100);
		QueryPerformanceCounter(&qpc);
		execution_time = (qpc.QuadPart - liStart.QuadPart) * qpc_freq;
		if (time_limit && execution_time > time_limit) {
			TerminateProcess(hProcess, 0xDEADBEEF);
			tle_ = true;
			WaitForSingleObject(hProcess, INFINITE);
		}
		QueryInformationJobObject(hJob, JobObjectExtendedLimitInformation, &extLimit, sizeof extLimit, nullptr);
		memory_ = extLimit.PeakJobMemoryUsed;
		mle_ |= memory_limit && memory_ > memory_limit;
	}
	return 0;
}