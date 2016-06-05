#ifndef _THREAD_DUMPER
#define _THREAD_DUMPER

#include <Python.h>
#include "pythread.h"
#include "frameobject.h"

void print_err(const char *message, ...);

inline void dump_threads()
{
PyGILState_STATE gstate;
  gstate = PyGILState_Ensure();
    PyInterpreterState *i;
    for (i = PyInterpreterState_Head(); i != NULL; i = PyInterpreterState_Next(i)) {
        PyThreadState *t;
        for (t = PyInterpreterState_ThreadHead(i); t != NULL; t = PyThreadState_Next(t)) {
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
            print_err("\n");
        }
    }
  PyGILState_Release(gstate);
}

#endif