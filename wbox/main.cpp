#include "user.h"
#include "process.h"
#include <shlwapi.h>
#include <io.h>
#include <stdio.h>
#include <fcntl.h>
#include <iostream>

int wmain() {
	try {
		UserManager user_manager;
		JobbedProcessManager process;
		WCHAR szDirectory[MAX_PATH];

		GetModuleFileName(nullptr, szDirectory, MAX_PATH);
		*(PathFindFileName(szDirectory) - 1) = '\0';
		process.time(2).memory(65536 * 1024).processes(1).command(L"hello.exe").directory(szDirectory)
			.withLogin(user_manager.username(), user_manager.password());
		process.spawn();
		process.stdIn().close();
		process.stdErr().close();
		int ch, fd = _open_osfhandle((intptr_t) process.stdOut().detach(), _O_RDONLY);
		FILE *file = _fdopen(fd, "r");
		while ((ch = fgetc(file)) != EOF)
			putchar(ch);
	} catch (WindowsException &e) {
		std::cout << e.what() << '\n';
	}
}