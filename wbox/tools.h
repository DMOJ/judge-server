#pragma once

#ifndef id_1AB80237_6F9E_4EB1_9CDA_F0B79A1745C1
#define id_1AB80237_6F9E_4EB1_9CDA_F0B79A1745C1

#include <string>
#include <algorithm>
#include <windows.h>

template<class T>
std::wstring list2cmdline(T start, T end) {
	std::wstring result, bs_buf;

	while (start != end) {
		LPWSTR elem = *start;
		if (!result.empty())
			result.push_back(' ');

		size_t length = lstrlen(elem);
		bool needquote = !length || std::any_of(elem, elem + length, [](wchar_t ch) {
			return ch == ' ' || ch == '\t';
		});
		if (needquote)
			result.push_back('"');

		LPCWSTR c = elem;
		while (*c) {
			switch (*c) {
			case L'\\':
				bs_buf.push_back(L'\\');
				break;
			case L'"':
				result += bs_buf + bs_buf;
				bs_buf.clear();
				result += L"\\\"";
				break;
			default:
				if (!bs_buf.empty()) {
					result += bs_buf;
					bs_buf.clear();
				}
				result.push_back(*c);
			}
			++c;
		}

		if (!bs_buf.empty())
			result += bs_buf;

		if (needquote) {
			result += bs_buf;
			result.push_back('"');
		}

		bs_buf.clear();
		++start;
	}
	return result;
}

#endif