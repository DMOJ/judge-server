#include <unistd.h>
#include <sys/reboot.h>
#include <stdio.h>

int main() {
    if(reboot(RB_HALT) == -1) {
        perror("reboot");
    }
    return 0;
}
