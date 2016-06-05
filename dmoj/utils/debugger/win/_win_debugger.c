#include <windows.h>
#include "../_thread_dumper.h"

void print_err(const char *message, ...) {
    va_list args;
    va_start(args, message);
    vfprintf(stderr, message, args);
    va_end(args);
}

BOOL WINAPI CtrlHandler(DWORD fdwCtrlType)
{
    if(fdwCtrlType == CTRL_BREAK_EVENT)
    {
        dump_threads();
        return TRUE;
    }
    return FALSE;
}

static PyObject *debugger_setup(PyObject *self, PyObject *args) {
    PyObject *result = SetConsoleCtrlHandler(CtrlHandler, TRUE) ? Py_True : Py_False;
    Py_INCREF(result);
    return result;
}

static PyMethodDef setup_methods[] = {
    {"setup_native_traceback", debugger_setup, METH_VARARGS, "Ctrl+Break debugger."},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC init_win_debugger(void) {
    (void) Py_InitModule("_win_debugger", setup_methods);
}
