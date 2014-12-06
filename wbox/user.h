#pragma once

#ifndef id_96499B6B_4A3F_4FF6_8C52_2BD6B4FB7233
#define id_96499B6B_4A3F_4FF6_8C52_2BD6B4FB7233

#include "helpers.h"
#include <windows.h>
#include <lm.h>

LPCWSTR wbox_password_alphabet = L"1234567890`~!@#$%^&*()-=_+{}[]|;:'<>?,./QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm";
void WBoxGenerateUserName(LPWSTR szUsername, size_t cchLength);
void WBoxGeneratePassword(LPWSTR szPassword, size_t cchLength, LPCWSTR szAlphabet=wbox_password_alphabet);

class UserManager {
	bool allow_existing, created;
	USER_INFO_1 ui1User;
	WCHAR szUsername[21];
	WCHAR szPassword[LM20_PWLEN + 1];
	void create_user() throw(WindowsException);
public:
	UserManager() throw(WindowsException);
	UserManager(LPCWSTR szUsername) throw(WindowsException);
	UserManager(LPCWSTR szUsername, LPCWSTR szPassword) throw(WindowsException);
	~UserManager();

	LPCWSTR username() { return szUsername; }
	LPCWSTR password() { return szPassword; }
};

#endif