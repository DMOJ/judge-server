#include "helpers.h"
#include <sstream>
#include <strsafe.h>

std::string FormatWindowsError(DWORD error) {
	LPSTR message = nullptr;
	if (FormatMessageA(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM, nullptr, error, 0, (LPSTR) &message, 1033, nullptr)) {
		std::string str(message);
		LocalFree(message);
		return str;
	}
	std::stringstream ss;
	ss << error;
	return ss.str();
}

WindowsException::WindowsException(const char* location) :
	error(GetLastError()), location(location) {
	message[0] = '\0';
}

WindowsException::WindowsException(const char* location, DWORD error) :
	error(error), location(location) {
	message[0] = '\0';
}

const char* WindowsException::what() const {
	if (!message[0])
		StringCchPrintfA(message, ARRAYSIZE(message), "%s: %d", location, error);
	return message;
}

SeDebugPrivilege::SeDebugPrivilege() {
	if (!OpenProcessToken(GetCurrentProcess(), TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, &hToken))
		throw WindowsException("OpenProcessToken");

	tp.PrivilegeCount = 1;
	tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED;

	if (!LookupPrivilegeValue(nullptr, SE_DEBUG_NAME, &tp.Privileges[0].Luid))
		throw WindowsException("LookupPrivilegeValue SE_DEBUG_NAME");

	if (!AdjustTokenPrivileges(hToken, FALSE, &tp, 0, nullptr, nullptr))
		throw WindowsException("AdjustTokenPrivileges");
}

SeDebugPrivilege::~SeDebugPrivilege() {
	tp.Privileges[0].Attributes = 0;

	if (!AdjustTokenPrivileges(hToken, FALSE, &tp, 0, nullptr, nullptr))
		throw WindowsException("AdjustTokenPrivileges");
}

HRException::HRException(const char* location, HRESULT error):
		error(error), location(location) {}

const char* HRException::what() const {
	if (!message[0])
		StringCchPrintfA(message, ARRAYSIZE(message), "%s: 0x%08X", location, error);
	return message;
}
