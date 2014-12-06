#include "helpers.h"
#include <sstream>

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

WindowsException::WindowsException(const char* location, DWORD error) :
	win_message(FormatWindowsError(error)),
	full_message(std::string(location) + ": " + win_message) {
}