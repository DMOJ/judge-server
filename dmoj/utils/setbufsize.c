#include <stdio.h>
#include <stdlib.h>

void _DMOJ_setbuffersize(void) __attribute__((constructor));

void _DMOJ_setbuffer(FILE *handle, char *env_str) {
    char *buf_env_str = getenv(env_str);
    if (buf_env_str != NULL) {
        char *end;
        unsigned long buf_size = strtoul(buf_env_str, &end, 10);
        if (*end == NULL) {
            // Need this branch since IOFBF when buf_size=0 actually
            // sets the buffer size to an OS-preferred, nonzero buffer
            if (buf_size) {
                setvbuf(handle, NULL, _IOFBF, buf_size);
            } else {
                setvbuf(handle, NULL, _IONBF, 0);
            }
        }
    }
}

void _DMOJ_setbuffersize(void) {
    _DMOJ_setbuffer(stdout, "CPTBOX_STDOUT_BUFFER_SIZE");
    _DMOJ_setbuffer(stderr, "CPTBOX_STDERR_BUFFER_SIZE");
}
