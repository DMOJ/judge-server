#pragma once

#ifndef id_26FCBE24_1243_4829_89F4_B266B158236E
#define id_26FCBE24_1243_4829_89F4_B266B158236E

#include <windows.h>
#include <exception>
#include <string>


#if defined(_MSC_VER) && _MSC_VER < 1600
const class nullptr_t {
public:
    template<class T>
    inline operator T*() const // convertible to any type of null non-member pointer...
    { return 0; }

    template<class C, class T>
    inline operator T C::*() const   // or any type of null member pointer...
    { return 0; }

private:
    void operator&() const;  // Can't take address of nullptr
} nullptr = {};
#endif


class AutoHandle {
	HANDLE handle;
public:
	AutoHandle() : handle(nullptr) {}
	explicit AutoHandle(HANDLE h) : handle(h) {}
	~AutoHandle() { CloseHandle(handle); }
	operator HANDLE() { return handle; }
	HANDLE get() { return handle; }
	void set(HANDLE h) { *this = h; }

	AutoHandle &operator=(HANDLE h) {
		if (handle)
			CloseHandle(handle);
		handle = h;
		return *this;
	}

	HANDLE detach() {
		HANDLE h = handle;
		handle = nullptr;
		return h;
	}

	void close() {
		CloseHandle(handle);
		handle = nullptr;
	}
};

class SeDebugPrivilege {
	HANDLE hToken;
	TOKEN_PRIVILEGES tp;
public:
	SeDebugPrivilege();
	~SeDebugPrivilege();
};

std::string FormatWindowsError(DWORD error);

class WindowsException : public std::exception {
	DWORD error;
	mutable char message[1024];
	const char *location;
public:
	WindowsException(const char* location);
	WindowsException(const char* location, DWORD error);
	const char* what() const override;
	DWORD code() { return error; }
};

class HRException : public std::exception {
	HRESULT error;
	mutable char message[1024];
	const char *location;
public:
	HRException(const char* location, HRESULT error);
	const char* what() const override;
	HRESULT code() { return error; }
};

inline void writeQword(BYTE *buf, DWORD64 qword)
{
    buf[0] = qword & 0xFF;
    buf[1] = (qword >> 8) & 0xFF;
    buf[2] = (qword >> 16) & 0xFF;
    buf[3] = (qword >> 24) & 0xFF;
    buf[4] = (qword >> 32) & 0xFF;
    buf[5] = (qword >> 40) & 0xFF;
    buf[6] = (qword >> 48) & 0xFF;
    buf[7] = (qword >> 56) & 0xFF;
}

inline void writeDword(BYTE *buf, DWORD dword)
{
    buf[0] = dword & 0xFF;
    buf[1] = (dword >> 8) & 0xFF;
    buf[2] = (dword >> 16) & 0xFF;
    buf[3] = (dword >> 24) & 0xFF;
}

#endif