#include <signal.h>
#include "../_thread_dumper.h"

void print_err(const char *message, ...) {
    char buffer[256];
    va_list args;
    va_start(args, message);
    vsnprintf(buffer, sizeof buffer, message, args);
    write(2, buffer, strlen(buffer));
    va_end(args);
}

static void print_traceback_on_sigusr1(int signum)
{
    dump_threads();
}

static PyObject *debugger_setup(PyObject *self, PyObject *args) {
    struct sigaction sa;
    sa.sa_handler = &print_traceback_on_sigusr1;
    sa.sa_flags = SA_RESTART;
    sigfillset(&sa.sa_mask);
    return sigaction(SIGUSR1, &sa, NULL) == -1 ? Py_False : Py_True;
}

static PyMethodDef setup_methods[] = {
    {"setup_native_traceback", debugger_setup, METH_VARARGS, "SIGUSR1 debugger."},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC init_debugger(void) {
    (void) Py_InitModule("_nix_debugger", setup_methods);
}
