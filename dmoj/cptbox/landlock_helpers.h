#include "landlock_header.h"

int landlock_add_rules(const int ruleset_fd, const char **paths, __u64 access_rule);
