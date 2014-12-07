#include "process.h"
#include "handles.h"
#include <objbase.h>
#include <strsafe.h>


JobbedProcessManager::JobbedProcessManager() :
		szUsername(nullptr), szPassword(nullptr), szDirectory(nullptr), szCmdLine(nullptr) {
	ZeroMemory(&extLimits, sizeof extLimits);
	extLimits.BasicLimitInformation.ActiveProcessLimit = 1;
	extLimits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_ACTIVE_PROCESS;
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

	if (!(handle = SearchForJob(hProcess, L"svchost.exe")))
		throw WindowsException("Failed to find job", 0);

	hJob = handle;
	if (!SetInformationJobObject(hJob, JobObjectExtendedLimitInformation, &extLimits, sizeof extLimits))
		throw WindowsException("SetInformationJobObject");

	ResumeThread(pi.hThread);
	CloseHandle(pi.hThread);
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
	} else
		extLimits.BasicLimitInformation.LimitFlags &= ~JOB_OBJECT_LIMIT_JOB_TIME;
	return *this;
}

JobbedProcessManager &JobbedProcessManager::memory(size_t bytes) {
	if (bytes) {
		extLimits.JobMemoryLimit = bytes;
		extLimits.BasicLimitInformation.LimitFlags |= JOB_OBJECT_LIMIT_JOB_MEMORY;
	} else
		extLimits.BasicLimitInformation.LimitFlags &= ~JOB_OBJECT_LIMIT_JOB_MEMORY;
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

JobbedProcessManager::~JobbedProcessManager() {
}
