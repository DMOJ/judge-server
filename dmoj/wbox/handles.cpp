#include <windows.h>
#include <tlhelp32.h>
#include <stdlib.h>

#include "handles.h"
#include "helpers.h"

#define NT_SUCCESS(x) ((x) >= 0)
#define STATUS_INFO_LENGTH_MISMATCH 0xc0000004

#define SystemHandleInformation 16
#define ObjectBasicInformation 0
#define ObjectNameInformation 1
#define ObjectTypeInformation 2

typedef LONG NTSTATUS, *PNTSTATUS;

typedef NTSTATUS(NTAPI *_NtQuerySystemInformation)(
	ULONG SystemInformationClass,
	PVOID SystemInformation,
	ULONG SystemInformationLength,
	PULONG ReturnLength
);

typedef NTSTATUS(NTAPI *_NtQueryObject)(
	HANDLE ObjectHandle,
	ULONG ObjectInformationClass,
	PVOID ObjectInformation,
	ULONG ObjectInformationLength,
	PULONG ReturnLength
);

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

typedef struct _UNICODE_STRING {
	USHORT Length;
	USHORT MaximumLength;
	PWSTR Buffer;
} UNICODE_STRING, *PUNICODE_STRING;

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

_NtQuerySystemInformation NtQuerySystemInformation = (_NtQuerySystemInformation) GetLibraryProcAddress("ntdll.dll", "NtQuerySystemInformation");
_NtQueryObject NtQueryObject = (_NtQueryObject) GetLibraryProcAddress("ntdll.dll", "NtQueryObject");


HANDLE SearchProcess(HANDLE hProcess, HANDLE hVictim, ULONG pid) {
	NTSTATUS status;
	PSYSTEM_HANDLE_INFORMATION handleInfo;
	ULONG handleInfoSize = 0x10000;
	ULONG i;
	HANDLE hJob = nullptr;

	handleInfo = (PSYSTEM_HANDLE_INFORMATION) malloc(handleInfoSize);

	/* NtQuerySystemInformation won't give us the correct buffer size,
	so we guess by doubling the buffer size. */
	while ((status = NtQuerySystemInformation(SystemHandleInformation, handleInfo, handleInfoSize, nullptr)) == STATUS_INFO_LENGTH_MISMATCH)
		handleInfo = (PSYSTEM_HANDLE_INFORMATION) realloc(handleInfo, handleInfoSize *= 2);

	/* NtQuerySystemInformation stopped giving us STATUS_INFO_LENGTH_MISMATCH. */
	if (!NT_SUCCESS(status))
		return fprintf(stderr, "NtQuerySystemInformation failed: %ld\n", status), nullptr;

	for (i = 0; i < handleInfo->HandleCount; i++) {
		SYSTEM_HANDLE &handle = handleInfo->Handles[i];
		HANDLE dupHandle = nullptr;
		POBJECT_TYPE_INFORMATION objectTypeInfo;

		/* Check if this handle belongs to the PID the user specified. */
		if (handle.ProcessId != pid)
			continue;

		/* Duplicate the handle so we can query it. */
		if (!DuplicateHandle(hVictim, (HANDLE) handle.Handle, GetCurrentProcess(), &dupHandle, JOB_OBJECT_ALL_ACCESS, 0, 0))
			continue;

		/* Query the object type. */
		objectTypeInfo = (POBJECT_TYPE_INFORMATION) malloc(0x1000);
		if (!NT_SUCCESS(NtQueryObject(dupHandle, ObjectTypeInformation, objectTypeInfo, 0x1000, nullptr))) {
			free(objectTypeInfo);
			CloseHandle(dupHandle);
			continue;
		}

		if (lstrcmpW(objectTypeInfo->Name.Buffer, L"Job") == 0) {
			BOOL bInJob;
			if (!IsProcessInJob(hProcess, dupHandle, &bInJob)) {
				fprintf(stderr, "Process %u: IsProcessInJob failed: %d\n", pid, GetLastError());
				continue;
			}
			if (bInJob) {
				free(objectTypeInfo);
				hJob = dupHandle;
				break;
			}
		}
		free(objectTypeInfo);
		CloseHandle(dupHandle);
	}
	free(handleInfo);
	return hJob;
}

HANDLE SearchForJobByService(HANDLE hProcess, LPCWSTR szServiceName) {
	SC_HANDLE schManager, schService;
	SERVICE_STATUS_PROCESS ssp;
	DWORD dwError;
	if (!(schManager = OpenSCManager(nullptr, SERVICES_ACTIVE_DATABASE, 0)))
		throw WindowsException("OpenSCManager");
	if (!(schService = OpenService(schManager, szServiceName, SERVICE_QUERY_STATUS))) {
		CloseServiceHandle(schManager);
		throw WindowsException("OpenService");
	}
	BOOL status = QueryServiceStatusEx(schService, SC_STATUS_PROCESS_INFO, (LPBYTE)&ssp, sizeof ssp, &dwError);
	dwError = GetLastError();
	CloseServiceHandle(schManager);
	CloseServiceHandle(schService);
	if (!status)
		throw WindowsException("QueryServiceStatusEx", dwError);

	HANDLE handle;
	{
		SeDebugPrivilege debug;
		handle = OpenProcess(PROCESS_DUP_HANDLE, FALSE, ssp.dwProcessId);
		if (!handle)
			throw WindowsException("OpenProcess");
	}

	HANDLE result = SearchProcess(hProcess, handle, ssp.dwProcessId);
	CloseHandle(handle);
	return result;
}

HANDLE SearchForJobByProcess(HANDLE hProcess, LPCWSTR szParentName) {
	SeDebugPrivilege debug;
	AutoHandle hProcessSnap, hParent;
	HANDLE handle;
	PROCESSENTRY32 pe32;

	if ((handle = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)) == INVALID_HANDLE_VALUE)
		throw WindowsException("CreateToolhelp32Snapshot");
	hProcessSnap = handle;
	
	pe32.dwSize = sizeof(PROCESSENTRY32);
	if (!Process32First(hProcessSnap, &pe32))
		throw WindowsException("CreateToolhelp32Snapshot");

	do {
		if (lstrcmp(pe32.szExeFile, szParentName) == 0) {
			if (!(handle = OpenProcess(PROCESS_DUP_HANDLE, FALSE, pe32.th32ProcessID)))
				fprintf(stderr, "Process %u: OpenProcess failed: %d\n", pe32.th32ProcessID, GetLastError());
			else {
				hParent = handle;
				HANDLE hResult = SearchProcess(hProcess, hParent, pe32.th32ProcessID);
				if (hResult)
					return hResult;
			}
		}
	} while (Process32Next(hProcessSnap, &pe32));
	return nullptr;
}
