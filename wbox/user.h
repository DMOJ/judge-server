#pragma once

#ifndef id_96499B6B_4A3F_4FF6_8C52_2BD6B4FB7233
#define id_96499B6B_4A3F_4FF6_8C52_2BD6B4FB7233

#include "helpers.h"
#include <windows.h>
#include <lm.h>

extern LPCWSTR wbox_password_alphabet;
void WBoxGenerateUserName(LPWSTR szUsername, size_t cchLength);
void WBoxGeneratePassword(LPWSTR szPassword, size_t cchLength, LPCWSTR szAlphabet=wbox_password_alphabet);

class UserManager {
	bool allow_existing, created;
	WCHAR szUsername[21];
	WCHAR szPassword[LM20_PWLEN + 1];
	void create_user();
public:
	UserManager();
	UserManager(LPCWSTR szUsername);
	UserManager(LPCWSTR szUsername, LPCWSTR szPassword);
	~UserManager();

	LPCWSTR username() { return szUsername; }
	LPCWSTR password() { return szPassword; }
};

#endif