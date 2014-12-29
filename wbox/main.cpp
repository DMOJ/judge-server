#include "user.h"
#include "process.h"
#include "firewall.h"
#include <shlwapi.h>
#include <io.h>
#include <stdio.h>
#include <fcntl.h>
#include <iostream>

int wmain() {
	try {
		UserManager user_manager;
		JobbedProcessManager process;
		WCHAR szDirectory[MAX_PATH], szExecutable[MAX_PATH];

		GetModuleFileName(nullptr, szDirectory, MAX_PATH);
		*(PathFindFileName(szDirectory) - 1) = '\0';
		PathCombine(szExecutable, szDirectory, L"hello.exe");

		NetworkManager network(L"wbox test", szExecutable);
		process.time(2).memory(65536 * 1024).processes(1).command(L"hello.exe").directory(szDirectory)
			.withLogin(user_manager.username(), user_manager.password()).executable(szExecutable);
		process.spawn();
		process.stdIn().close();
		process.stdErr().close();
		int ch, fd = _open_osfhandle((intptr_t) process.stdOut().detach(), _O_RDONLY);
		FILE *file = _fdopen(fd, "r");
		while ((ch = fgetc(file)) != EOF)
			putchar(ch);
		process.wait();
		printf("Memory usage: %.2f MiB\n", process.memory() / 1024. / 1024.);
		printf("Time usage: %.3fs\n", process.executionTime());
		printf("Return: %lu\n", process.return_code());
	} catch (WindowsException &e) {
		std::cout << e.what() << '\n';
	}
}