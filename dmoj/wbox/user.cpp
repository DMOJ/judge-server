#include "user.h"
#include <stdlib.h>
#include <strsafe.h>

LPCWSTR wbox_password_alphabet = L"1234567890`~!@#$%^&*()-=_+{}[]|;:'<>?,./QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm";

void WBoxGenerateUserName(LPWSTR szUsername, size_t cchLength) {
	LUID luid;
	AllocateLocallyUniqueId(&luid);
	StringCchPrintf(szUsername, cchLength, L"wbox%08lx%08lx", (DWORD) luid.HighPart, luid.LowPart);
}

void WBoxGeneratePassword(LPWSTR szPassword, size_t cchLength, LPCWSTR szAlphabet) {
	size_t cchAlphabet = lstrlen(szAlphabet);
	unsigned random;
	for (size_t i = 0; i < cchLength - 1; ++i) {
#ifdef _CRT_RAND_S
		rand_s(&random);
#else
		random = rand();
#endif
		szPassword[i] = szAlphabet[random % cchAlphabet];
	}
	szPassword[cchLength - 1] = '\0';
}

void UserManager::create_user() {
	USER_INFO_1 ui1User;
	ZeroMemory(&ui1User, sizeof ui1User);
	ui1User.usri1_name = szUsername;
	ui1User.usri1_password = szPassword;
	ui1User.usri1_priv = USER_PRIV_USER;
	ui1User.usri1_flags = UF_PASSWD_CANT_CHANGE | UF_SCRIPT | UF_DONT_EXPIRE_PASSWD;
	NET_API_STATUS status = NetUserAdd(nullptr, 1, (LPBYTE) &ui1User, nullptr);
	if (status == NERR_UserExists) {
		if (!allow_existing)
			throw WindowsException("NetUserAdd", status);
	} else if (status != NERR_Success)
		throw WindowsException("NetUserAdd", status);
	else
		created = true;

	LOCALGROUP_MEMBERS_INFO_3 lmi3;
	ZeroMemory(&lmi3, sizeof lmi3);
	lmi3.lgrmi3_domainandname = szUsername;
	status = NetLocalGroupAddMembers(nullptr, L"Users", 3, (LPBYTE) &lmi3, 1);
	if (status != NERR_Success)
		throw WindowsException("NetLocalGroupAddMembers", status);
}

UserManager::UserManager() : allow_existing(false), created(false) {
	WBoxGenerateUserName(szUsername, ARRAYSIZE(szUsername));
	WBoxGeneratePassword(szPassword, ARRAYSIZE(szPassword));
	create_user();
}

UserManager::UserManager(LPCWSTR szUsername) : allow_existing(false), created(false) {
	StringCchCopy(this->szUsername, ARRAYSIZE(this->szUsername), szUsername);
	WBoxGeneratePassword(szPassword, ARRAYSIZE(szPassword));
	create_user();
}

UserManager::UserManager(LPCWSTR szUsername, LPCWSTR szPassword) : allow_existing(true), created(false) {
	StringCchCopy(this->szUsername, ARRAYSIZE(this->szUsername), szUsername);
	StringCchCopy(this->szPassword, ARRAYSIZE(this->szPassword), szPassword);
	create_user();
}

UserManager::~UserManager() {
	if (created && !allow_existing)
		NetUserDel(nullptr, szUsername);
}
