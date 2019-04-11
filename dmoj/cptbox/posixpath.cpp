#include "posixpath.h"
#include <iterator>
#include <string>
#include <sstream>
#include <vector>

// Borrowed from https://stackoverflow.com/a/5289170/1090657
template <typename Range, typename Value = typename Range::value_type>
std::string string_join(Range const& elements, const char * delimiter) {
    std::ostringstream os;
    auto b = std::begin(elements), e = std::end(elements);

    if (b != e) {
        std::copy(b, prev(e), std::ostream_iterator<Value>(os, delimiter));
        b = prev(e);
    }

    if (b != e) {
        os << *b;
    }

    return os.str();
}

namespace posixpath {
    std::string join(const std::string &parent, const std::string &child) {
        if (!child.empty() && child[0] == '/') {
            return child;
        }
        if (parent.empty() || parent.back() == '/') {
            return parent + child;
        } else {
            return parent + "/" + child;
        }
    }

    std::string normpath(const std::string &path) {
        if (path.empty()) {
            return ".";
        }

        bool absolute = path[0] == '/';
        std::istringstream stream(path);
        std::string token;
        std::vector<std::string> comps;

        while (std::getline(stream, token, '/')) {
            if (token.empty() || token == ".")
                continue;
            if (token != ".." || (!absolute && comps.empty()) ||
                    (!comps.empty() && comps.back() == "..")) {
                comps.push_back(token);
            } else if (!comps.empty()) {
                comps.pop_back();
            }
        }

        auto result = string_join(comps, "/");
        return absolute ? "/" + result : result;
    }
}
