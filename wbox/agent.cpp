#include <windows.h>
#include <iostream>
#include <strsafe.h>
#include "helpers.h"
#include "tools.h"


int wmain(int argc, wchar_t *argv[]) {
	if (argc < 3)
		return 2;

	HANDLE handle;
	LPWSTR szGuid = argv[1];
	WCHAR szName[MAX_PATH];

	std::wstring cmdline = list2cmdline(argv + 2, argv + argc);
	std::wcout << cmdline << '\n';

	try {
		StringCchCopy(szName, MAX_PATH, L"wbox_job_");
		StringCchCat(szName, MAX_PATH, szGuid);
		if (!(handle = OpenJobObject(JOB_OBJECT_ASSIGN_PROCESS, FALSE, szName)))
			throw WindowsException("OpenJobObject");

		AutoHandle hJob(handle);
		STARTUPINFO si = { sizeof(STARTUPINFO), 0 };
		PROCESS_INFORMATION pi;

		if (!CreateProcess(nullptr, &cmdline.front(), nullptr, nullptr, FALSE,
						   NORMAL_PRIORITY_CLASS | CREATE_SUSPENDED | CREATE_BREAKAWAY_FROM_JOB,
						   nullptr, nullptr, &si, &pi))
			throw WindowsException("CreateProcess");

		AssignProcessToJobObject(hJob, pi.hProcess);
		CloseHandle(pi.hProcess);
		CloseHandle(pi.hThread);

		return pi.dwProcessId;
	} catch (WindowsException &e) {
		std::cout << e.what() << '\n';
	}
}
