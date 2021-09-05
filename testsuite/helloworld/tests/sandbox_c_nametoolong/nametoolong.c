#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

int main() {
    char buf[4352];
    memset(buf, 'a', sizeof buf - 1);
    for (int i = 0; i < sizeof buf; i += 256)
        buf[i] = '/';
    buf[sizeof buf - 1] = '\0';

    int fd;
    if ((fd = open(buf, O_RDONLY)) >= 0) {
        close(fd);
        puts("Should not open the file");
    } else if (errno == ENAMETOOLONG) {
        puts("Hello, World!");
    } else {
        printf("Wrong errno: %d", errno);
    }
}
