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

WindowsException::WindowsException(const char* location, DWORD error) :
	error(error), location(location) {
	message[0] = '\0';
}

const char* WindowsException::what() const {
	if (!message[0])
		StringCchPrintfA(message, ARRAYSIZE(message), "%s: %d", location, error);
	return message;
}