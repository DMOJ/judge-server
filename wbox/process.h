#pragma once

#ifndef id_83DB5799_5792_4F64_BC72_4086C9C0C735
#define id_83DB5799_5792_4F64_BC72_4086C9C0C735

#include <windows.h>
#include <cinttypes>
#include "helpers.h"

class JobbedProcessManager {
	AutoHandle hProcess;
	AutoHandle hJob;
	AutoHandle hStdin, hStdout, hStderr;
	JOBOBJECT_EXTENDED_LIMIT_INFORMATION extLimits;
	JOBOBJECT_BASIC_UI_RESTRICTIONS uiLimits;
	GUID guid;
	WCHAR szGuid[40];
	LPCWSTR szUsername, szPassword, szDirectory, szExecutable;
	LPWSTR szCmdLine;
public:
	JobbedProcessManager();
	virtual ~JobbedProcessManager();

	virtual bool spawn();
	virtual bool terminate(unsigned code);

	JobbedProcessManager &time(double seconds);
	JobbedProcessManager &memory(size_t bytes);
	JobbedProcessManager &processes(int count);
	JobbedProcessManager &withLogin(LPCWSTR szUsername, LPCWSTR szPassword);
	JobbedProcessManager &command(LPCWSTR szCmdLine);
	JobbedProcessManager &executable(LPCWSTR szExecutable);
	JobbedProcessManager &directory(LPCWSTR szDirectory);

	AutoHandle &process() { return hProcess; }
	AutoHandle &job() { return hJob; }
	// stdin is apparently a macro. *facepalm*
	AutoHandle &stdIn() { return hStdin; }
	AutoHandle &stdOut() { return hStdout; }
	AutoHandle &stdErr() { return hStderr; }
};

#endif