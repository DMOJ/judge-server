#pragma once
#ifndef id2E2DA71A_EAAB_4454_927325D6475896EC
#define id2E2DA71A_EAAB_4454_927325D6475896EC

#include <string>

namespace posixpath {
    std::string join(const std::string &parent, const std::string &child);
    std::string normpath(const std::string &path);
}

#endif // id2E2DA71A_EAAB_4454_927325D6475896EC

