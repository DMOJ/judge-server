#pragma once
#ifndef id_45B7650F_B801_414B_85053F5264B45F30
#define id_45B7650F_B801_414B_85053F5264B45F30

#include <objbase.h>
#include <netfw.h>

#include <atlbase.h>

class CCoInitialize {
public:
	CCoInitialize() : m_hr(CoInitialize(nullptr)) { }
	~CCoInitialize() { if (SUCCEEDED(m_hr)) CoUninitialize(); }
	operator HRESULT() const { return m_hr; }
	HRESULT m_hr;
};

class NetworkManager {
	CCoInitialize com;
	CComPtr<INetFwPolicy2> pPolicy;
	CComPtr<INetFwRules> pRules;
	CComPtr<INetFwRule> pRule;
	CComBSTR bstrRuleName;
public:
	NetworkManager(LPCWSTR szRuleName, LPCWSTR szApplication);
	~NetworkManager();
};

#endif
