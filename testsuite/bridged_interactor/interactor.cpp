#include <cstdio>
#include <cstdlib>

inline void read(long long *i) {
    if(scanf("%lld", i) != 1 || *i < 1 || *i > 2000000000)
        exit(2);
}

int main(int argc, char* argv[]) {
    FILE *input_file = fopen(argv[1], "r");
    int N, guesses = 0;
    long long guess;
    fscanf(input_file, "%d", &N);
    while(guess != N) {
        read(&guess);
        if(guess == N) {
            puts("OK");
        } else if(guess > N) {
            puts("FLOATS");
        } else {
            puts("SINKS");
        }
        fflush(stdout);
        guesses++;
    }
    if(guesses <= 31)
        return 0; // AC
    else
        return 1; // WA
}
