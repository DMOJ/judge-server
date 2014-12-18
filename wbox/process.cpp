#include "process.h"
#include "handles.h"
#include <objbase.h>
#include <strsafe.h>


DWORD JobbedProcessManager::s_ShockerProc(LPVOID lpParam) {
	return static_cast<JobbedProcessManager*>(lpParam)->ShockerProc();
}

JobbedProcessManager::JobbedProcessManager() :
		szUsername(nullptr), szPassword(nullptr), szDirectory(nullptr), szCmdLine(nullptr),
		tle_(false), mle_(false), terminate_shocker(true) {
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
	si.dwFlags |= STARTF_USESTDHANDLES;

	if (!CreateProcessWithLogonW(szUsername, L".", szPassword, 0, szExecutable, szCmdLine,
								 NORMAL_PRIORITY_CLASS | CREATE_SUSPENDED | CREATE_BREAKAWAY_FROM_JOB,
								 nullptr, szDirectory, &si, &pi))
		throw WindowsException("CreateProcessWithLogonW");

	CloseHandle(si.hStdInput);
	CloseHandle(si.hStdOutput);
	CloseHandle(si.hStdError);
	hProcess = pi.hProcess;

	if (!(handle = SearchForJobByService(hProcess, L"seclogon")))
		throw WindowsException("Failed to find job", 0);

	hJob = handle;
	if (!SetInformationJobObject(hJob, JobObjectExtendedLimitInformation, &extLimits, sizeof extLimits))
		throw WindowsException("SetInformationJobObject JobObjectExtendedLimitInformation");

	if (!SetInformationJobObject(hJob, JobObjectBasicUIRestrictions, &uiLimits, sizeof uiLimits))
		throw WindowsException("SetInformationJobObject JobObjectBasicUIRestrictions");

	LARGE_INTEGER liFreq;
	QueryPerformanceFrequency(&liFreq);
	qpc_freq = 1 / liFreq.QuadPart;
	QueryPerformanceCounter(&liStart);
	ResumeThread(pi.hThread);
	CloseHandle(pi.hThread);

	if (!(handle = CreateThread(nullptr, 0, s_ShockerProc, this, 0, nullptr)))
		throw WindowsException("CreateThread");
	hShocker = handle;
	return true;
}

bool JobbedProcessManager::terminate(unsigned code) {
	if (hProcess)
		if (!TerminateProcess(hProcess, code))
			throw WindowsException("TerminateProcess");
	return false;
}

JobbedProcessManager &JobbedProcessManager::time(double seconds) {
	if (seconds) {
		extLimits.BasicLimitInformation.PerJobUserTimeLimit.QuadPart = uint64_t(seconds * 1000 * 1000 * 10);
		extLimits.BasicLimitInformation.LimitFlags |= JOB_OBJECT_LIMIT_JOB_TIME;
		time_limit = unsigned long long(seconds * 1000);
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

JobbedProcessManager& JobbedProcessManager::withLogin(LPCWSTR szUsername, LPCWSTR szPassword) {
	this->szUsername = szUsername;
	this->szPassword = szPassword;
	return *this;
}

JobbedProcessManager& JobbedProcessManager::command(LPCWSTR szCmdLine) {
	if (this->szCmdLine)
		free(this->szCmdLine);
	size_t bytes = (lstrlen(szCmdLine) + 1) * sizeof(WCHAR);
	this->szCmdLine = (LPWSTR) malloc(bytes);
	StringCbCopy(this->szCmdLine, bytes, szCmdLine);
	return *this;
}

JobbedProcessManager& JobbedProcessManager::executable(LPCWSTR szExecutable) {
	this->szExecutable = szExecutable;
	return *this;
}

JobbedProcessManager& JobbedProcessManager::directory(LPCWSTR szDirectory) {
	this->szDirectory = szDirectory;
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
	
	do {
		QueryPerformanceCounter(&qpc);
		execution_time = (qpc.QuadPart - liStart.QuadPart) * qpc_freq;
		if (time_limit && execution_time * 1000 > time_limit) {
			TerminateProcess(hProcess, 0xDEADBEEF);
			tle_ = true;
			WaitForSingleObject(hProcess, INFINITE);
		}
		QueryInformationJobObject(hJob, JobObjectExtendedLimitInformation, &extLimit, sizeof extLimit, nullptr);
		memory_ = extLimit.PeakJobMemoryUsed;
		mle_ |= memory_limit && memory_ > memory_limit;
		Sleep(100);
	} while (!terminate_shocker && WaitForSingleObject(hProcess, 0) == WAIT_TIMEOUT);
	return 0;
}