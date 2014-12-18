#pragma once

#ifndef id_83DB5799_5792_4F64_BC72_4086C9C0C735
#define id_83DB5799_5792_4F64_BC72_4086C9C0C735

#include <windows.h>
#include <cinttypes>
#include "helpers.h"

class JobbedProcessManager {
	AutoHandle hProcess, hShocker;
	AutoHandle hJob;
	AutoHandle hStdin, hStdout, hStderr;
	JOBOBJECT_EXTENDED_LIMIT_INFORMATION extLimits;
	JOBOBJECT_BASIC_UI_RESTRICTIONS uiLimits;
	GUID guid;
	WCHAR szGuid[40];
	LPCWSTR szUsername, szPassword, szDirectory, szExecutable;
	LPWSTR szCmdLine;
	bool tle_, mle_, terminate_shocker;
	unsigned long long memory_, time_limit, memory_limit;
	DWORD cpu_time_;
	LARGE_INTEGER liStart;
	double qpc_freq, execution_time;

	static DWORD CALLBACK s_ShockerProc(LPVOID lpParam);
	DWORD CALLBACK ShockerProc();
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

	unsigned long long memory() { return memory_; }
	double executionTime() { return execution_time; }
	bool tle() { return tle_; }
	bool mle() { return mle_; }
	DWORD return_code();
	bool wait(DWORD time = INFINITE);

	AutoHandle &process() { return hProcess; }
	AutoHandle &job() { return hJob; }
	// stdin is apparently a macro. *facepalm*
	AutoHandle &stdIn() { return hStdin; }
	AutoHandle &stdOut() { return hStdout; }
	AutoHandle &stdErr() { return hStderr; }
};

#endif