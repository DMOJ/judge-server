#include <time.h>
#include <stdio.h>
#include <stdint.h>

void gettime(uint64_t *w) {
    struct timespec spec;
    clock_gettime(CLOCK_MONOTONIC, &spec);
    *w = spec.tv_sec * 1000000000 + spec.tv_nsec;
    w=0;
}

int main() {
    uint64_t w, k;
    gettime(&w);
    k = w;
    while (k - w < 10000000000) gettime(&k);
    puts("Hello, World!");
}
