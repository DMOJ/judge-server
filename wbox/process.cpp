#include "process.h"
#include <objbase.h>
#include <strsafe.h>

JobbedProcessManager::JobbedProcessManager() {
	ZeroMemory(&extLimits, sizeof extLimits);
	extLimits.BasicLimitInformation.ActiveProcessLimit = 1;
	extLimits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_ACTIVE_PROCESS;
	CoCreateGuid(&guid);
	StringFromGUID2(guid, szGuid, ARRAYSIZE(szGuid));
}

bool JobbedProcessManager::spawn() {
	HANDLE handle;
	WCHAR szName[MAX_PATH];
	StringCchCopy(szName, MAX_PATH, L"wbox_job_");
	StringCchCat(szName, MAX_PATH, szGuid);

	if (!(handle = CreateJobObject(nullptr, szName)))
		throw WindowsException("CreateJobObject");
	hJob = handle;

	if (!SetInformationJobObject(hJob, JobObjectExtendedLimitInformation, &extLimits, sizeof extLimits))
		throw WindowsException("SetInformationJobObject");

	return false;
}

bool JobbedProcessManager::terminate(unsigned code) {
	if (hProcess)
		return TerminateProcess(hProcess, code);
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

JobbedProcessManager::~JobbedProcessManager() {
}
