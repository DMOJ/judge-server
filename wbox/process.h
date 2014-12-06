#pragma once

#ifndef id_83DB5799_5792_4F64_BC72_4086C9C0C735
#define id_83DB5799_5792_4F64_BC72_4086C9C0C735

#include <windows.h>
#include <cinttypes>
#include "helpers.h"

void WBoxSetAgent(LPWSTR szPath);

class JobbedProcessManager {
	AutoHandle hProcess;
	AutoHandle hJob;
	JOBOBJECT_EXTENDED_LIMIT_INFORMATION extLimits;
	GUID guid;
	WCHAR szGuid[40];
	LPCWSTR szUsername, szPassword, szDirectory;
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
	JobbedProcessManager &directory(LPCWSTR szDirectory);

	HANDLE process() { return hProcess; }
	HANDLE job() { return hJob; }
};

#endif