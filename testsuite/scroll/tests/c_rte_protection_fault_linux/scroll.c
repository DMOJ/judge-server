#include <unistd.h>
#include <sys/reboot.h>
#include <stdio.h>
#include <linux/reboot.h>

int main() {
    if(reboot(LINUX_REBOOT_CMD_HALT) == -1) {
        perror("reboot");
    }
    return 0;
}
