#include "process.h"


JobbedProcessManager::JobbedProcessManager() {
}


bool JobbedProcessManager::spawn() {
	
}

bool JobbedProcessManager::terminate(unsigned code) {
	if (hProcess)
		return TerminateProcess(hProcess, code);
	return false;
}

JobbedProcessManager::~JobbedProcessManager() {
}
