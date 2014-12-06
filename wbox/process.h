#pragma once

#ifndef id_83DB5799_5792_4F64_BC72_4086C9C0C735
#define id_83DB5799_5792_4F64_BC72_4086C9C0C735

#include <windows.h>
#include <cinttypes>
#include "helpers.h"

class JobbedProcessManager {
	AutoHandle hProcess;
	AutoHandle hJob;
	JOBOBJECT_EXTENDED_LIMIT_INFORMATION extLimits;
	GUID guid;
	WCHAR szGuid[40];
public:
	JobbedProcessManager();
	virtual ~JobbedProcessManager();

	virtual bool spawn();
	virtual bool terminate(unsigned code);

	JobbedProcessManager &time(double seconds);
	JobbedProcessManager &memory(size_t bytes);
	JobbedProcessManager &processes(int count);

	HANDLE process() { return hProcess; }
	HANDLE job() { return hJob; }
};

#endif