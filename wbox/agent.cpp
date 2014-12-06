#include <windows.h>
#include <iostream>
#include <strsafe.h>
#include "helpers.h"
#include "tools.h"


int wmain(int argc, wchar_t *argv[]) {
	if (argc < 3)
		return 2;

	LPWSTR szGuid = argv[1];
	WCHAR szName[MAX_PATH];

	std::wstring cmdline = list2cmdline(argv + 2, argv + argc);
	std::wcout << cmdline << '\n';

	try {
		STARTUPINFO si = { sizeof(STARTUPINFO), 0 };
		PROCESS_INFORMATION pi;

		if (!CreateProcess(nullptr, &cmdline.front(), nullptr, nullptr, FALSE,
						   NORMAL_PRIORITY_CLASS | CREATE_SUSPENDED | CREATE_BREAKAWAY_FROM_JOB,
						   nullptr, nullptr, &si, &pi))
			throw WindowsException("CreateProcess");

		CloseHandle(pi.hProcess);
		CloseHandle(pi.hThread);

		return pi.dwProcessId;
	} catch (WindowsException &e) {
		std::cout << e.what() << '\n';
		getchar();
		return -(int)e.code();
	}
}
