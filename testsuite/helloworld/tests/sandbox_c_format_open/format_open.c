#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>

int main() {
    int fd;
    if ((fd = open("%s", O_RDONLY)) >= 0) {
        puts("Should not open the file");
    } else if (errno == EACCES || errno == ENOENT) { // differs between seccomp and landlock
        puts("Hello, World!");
        return 0;
    } else {
        printf("Wrong errno: %d", errno);
    }
    return -1;
}
