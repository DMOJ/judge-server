#include "firewall.h"
#include "helpers.h"

static CComBSTR bstrRuleDescription(L"Blocks an application from accessing the network in wbox");
static CComBSTR bstrRuleGroup(L"wbox block");
static CComBSTR bstrRuleLPorts(L"all");

NetworkManager::NetworkManager(LPCWSTR szRuleName, LPCWSTR szApplication):
		bstrRuleName(szRuleName) {
	HRESULT hr;
	long lProfileMask = 0;

	if (FAILED(hr = pPolicy.CoCreateInstance(CLSID_NetFwPolicy2)))
		throw HRException("CoCreateInstance NetFwPolicy2", hr);
	if (FAILED(hr = pPolicy->get_Rules(&pRules)))
		throw HRException("NetFwPolicy2->get_Rules", hr);
	if (FAILED(hr = pPolicy->get_CurrentProfileTypes(&lProfileMask)))
		throw HRException("NetFwPolicy2->get_CurrentProfileTypes", hr);
	
	CComBSTR bstrRuleApplication(szApplication);
	if (FAILED(hr = pRule.CoCreateInstance(CLSID_NetFwRule)))
		throw HRException("CoCreateInstance NetFwRule", hr);

	pRule->put_Name(bstrRuleName);
	pRule->put_Description(bstrRuleDescription);
	pRule->put_ApplicationName(bstrRuleApplication);
	pRule->put_Protocol(NET_FW_IP_PROTOCOL_TCP);
	pRule->put_LocalPorts(bstrRuleLPorts);
	pRule->put_Direction(NET_FW_RULE_DIR_OUT);
	pRule->put_Grouping(bstrRuleGroup);
	pRule->put_Profiles(lProfileMask);
	pRule->put_Action(NET_FW_ACTION_BLOCK);
	pRule->put_Enabled(VARIANT_TRUE);

	if (FAILED(hr = pRules->Add(pRule)))
		throw HRException("INetFwRules->Add", hr);
}

NetworkManager::~NetworkManager() {
	pRules->Remove(bstrRuleName);
}