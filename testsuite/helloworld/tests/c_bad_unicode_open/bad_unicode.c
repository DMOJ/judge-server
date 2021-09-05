#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

int main() {
    int fd;
    if ((fd = open("\xaa", O_RDONLY)) >= 0) {
        close(fd);
        puts("Should not open the file");
    } else if (errno == ENOENT) {
        puts("Hello, World!");
    } else {
        printf("Wrong errno: %d", errno);
    }
}
