#include <Python.h>
#include "pythread.h"
#include "frameobject.h"
#include <cstdio>
#include <signal.h>

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
    for (PyInterpreterState *i = PyInterpreterState_Head(); i != NULL; i = PyInterpreterState_Next(i)) {
        for (PyThreadState *t = PyInterpreterState_ThreadHead(i); t != NULL; t = PyThreadState_Next(t)) {
            PyFrameObject *frame = t->frame;
            if (frame == NULL)
                continue;

            print_err("# Thread %ld (most recent call first):\n", t->thread_id);

            do {
                int line = frame->f_lineno;
                const char *file_name = PyString_AsString(frame->f_code->co_filename);
                const char *func_name = PyString_AsString(frame->f_code->co_name);
                print_err("   File: \"%s\", line %d, in %s\n", file_name, line, func_name);
            } while ((frame = frame->f_back) != NULL);
            print_err("\n")
        }
    }
}

static PyObject *debugger_setup(PyObject *self, PyObject *args) {
    struct sigaction sa;
    sa.sa_handler = &print_traceback_on_sigusr1;
    sa.sa_flags = SA_RESTART;
    sigfillset(&sa.sa_mask);
    if(sigaction(SIGUSR1, &sa, NULL) == -1)
        fprintf(stderr, "Error: cannot handle SIGUSR1\n");  // TODO: raising exception might be more appropriate
    return Py_BuildValue("");
}

static PyObject *debugger_hang(PyObject *self, PyObject *args) {
    while (1);
    return Py_BuildValue("");
}

static PyMethodDef setup_methods[] = {
    {"setup_native_traceback", debugger_setup, METH_VARARGS, "SIGUSR1 debugger."},
    {"hang", debugger_hang, METH_VARARGS, "Hang forever."},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC init_debugger(void) {
    (void) Py_InitModule("_debugger", setup_methods);
}