#pragma once

#ifndef id_83DB5799_5792_4F64_BC72_4086C9C0C735
#define id_83DB5799_5792_4F64_BC72_4086C9C0C735

#include <windows.h>
#include "helpers.h"

class JobbedProcessManager {
	AutoHandle hProcess;
	AutoHandle hJob;
public:
	JobbedProcessManager();
	virtual ~JobbedProcessManager();

	virtual bool spawn();
	virtual bool terminate(unsigned code);

	HANDLE process() { return hProcess; }
	HANDLE job() { return hJob; }
};

#endif