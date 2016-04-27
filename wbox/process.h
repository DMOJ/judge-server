#pragma once

#ifndef id_83DB5799_5792_4F64_BC72_4086C9C0C735
#define id_83DB5799_5792_4F64_BC72_4086C9C0C735

#include <windows.h>
#include <cinttypes>
#include "helpers.h"
#include "getaddr.h"

class JobbedProcessManager {
	AutoHandle hProcess, hShocker;
	AutoHandle hJob;
	AutoHandle hStdin, hStdout, hStderr;
	JOBOBJECT_EXTENDED_LIMIT_INFORMATION extLimits;
	JOBOBJECT_BASIC_UI_RESTRICTIONS uiLimits;
	GUID guid;
	WCHAR szGuid[40];
	LPWSTR szUsername, szPassword, szDirectory, szExecutable, szEnvBlock;
	LPWSTR szCmdLine, szInjectX86, szInjectX64;
    LPSTR szInjectFunction;
	bool tle_, mle_, terminate_shocker;
	unsigned long long memory_, memory_limit;
	DWORD cpu_time_;
	LARGE_INTEGER liStart;
	double qpc_freq, execution_time, time_limit;

	static DWORD CALLBACK s_ShockerProc(LPVOID lpParam);
	DWORD CALLBACK ShockerProc();
    
    static bool canX86, canX64;
    
    static struct _init {
        _init() {
            SYSTEM_INFO si;
            
            GetNativeSystemInfo(&si);
            switch (si.wProcessorArchitecture) {
#ifdef _WIN64
                case PROCESSOR_ARCHITECTURE_AMD64:
                    canX64 = TRUE;
#endif
                case PROCESSOR_ARCHITECTURE_INTEL:
                    canX86 = TRUE;
                    break;
            }
        }
    } _initializer;

    static BYTE asmX86[], asmX64[];
    static bool inject(HANDLE hProcess, BOOL x64, LPCWSTR szDllPath, LPCSTR szFunctionName);
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
	JobbedProcessManager &injectX86(LPCWSTR szExecutable);
	JobbedProcessManager &injectX64(LPCWSTR szExecutable);
	JobbedProcessManager &injectFunction(LPCSTR szFunction);
	JobbedProcessManager &environment(LPCWSTR szEnvBlock, size_t cbBytes);

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
    
    static void updateAsmX86(LPCWSTR szExecutable);
    static void updateAsmX64(LPCWSTR szExecutable);
};

#endif