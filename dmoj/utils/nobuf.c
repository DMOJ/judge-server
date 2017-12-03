#include <stdio.h>

void _DMOJ_unbuffer(void) __attribute__((constructor));

void _DMOJ_unbuffer(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
}
