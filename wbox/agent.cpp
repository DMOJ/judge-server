#include <windows.h>
#include <iostream>
#include "tools.h"


int wmain(int argc, wchar_t *argv[]) {
	if (argc < 3)
		return 2;

	LPWSTR guid = argv[1];
	std::wstring cmdline = list2cmdline(argv + 2, argv + argc);
	std::wcout << cmdline << '\n';
}
