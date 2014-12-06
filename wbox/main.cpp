#include "user.h"
#include "process.h"
#include <shlwapi.h>

int wmain() {
	UserManager user_manager;
	JobbedProcessManager process;
	WCHAR szDirectory[MAX_PATH];

	GetModuleFileName(nullptr, szDirectory, MAX_PATH);
	*(PathFindFileName(szDirectory) - 1) = '\0';
	process.time(2).memory(65536 * 1024).processes(1).command(L"hello.exe").directory(szDirectory);
}