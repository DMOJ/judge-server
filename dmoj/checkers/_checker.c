#include <Python.h>

#define UNREFERENCED_PARAMETER(p)
#if defined(_MSC_VER)
#define inline __declspec(inline)
#pragma warning(disable : 4127)
#undef UNREFERENCED_PARAMETER
#define UNREFERENCED_PARAMETER(p) (p)
#elif !defined(__GNUC__)
#define inline
#endif

static inline int isline(char ch) {
    switch (ch) {
        case '\n':
        case '\r':
            return 1;
    }
    return 0;
}

static inline int iswhite(char ch) {
    switch (ch) {
        case ' ':
        case '\t':
        case '\v':
        case '\f':
        case '\n':
        case '\r':
            return 1;
    }
    return 0;
}

/* Increment *pos to the next non-whitespace character, and returns
 * 2 if a new line was seen, 1 if only spaces were seen, and 0 if no whitespace was seen */
static inline int skip_spaces(const char *str, size_t *pos, size_t length) {
    int saw_line = 0, saw_space = 0;
    while (*pos < length) {
        saw_line |= isline(str[*pos]);
        if (!iswhite(str[*pos])) {
            break;
        }
        ++*pos;
        saw_space = 1;
    }
    return saw_line ? 2 : saw_space;
}

static int check_standard(const char *judge, size_t jlen, const char *process, size_t plen) {
    size_t j = 0, p = 0;

    while (j < jlen && iswhite(judge[j]))
        ++j;
    while (p < plen && iswhite(process[p]))
        ++p;
    for (;;) {
        int js = skip_spaces(judge, &j, jlen);
        int ps = skip_spaces(process, &p, plen);
        if (j == jlen || p == plen)
            return j == jlen && p == plen;
        if (js != ps)
            return 0;

        while (j < jlen && !iswhite(judge[j])) {
            if (p >= plen)
                return 0;
            if (judge[j++] != process[p++])
                return 0;
        }
    }
}

static PyObject *checker_standard(PyObject *self, PyObject *args) {
    PyObject *expected, *actual, *result;

    UNREFERENCED_PARAMETER(self);
    if (!PyArg_ParseTuple(args, "OO:standard", &expected, &actual))
        return NULL;

    if (!PyBytes_Check(expected) || !PyBytes_Check(actual)) {
        PyErr_SetString(PyExc_ValueError, "expected strings");
        return NULL;
    }

    Py_INCREF(expected);
    Py_INCREF(actual);
    Py_BEGIN_ALLOW_THREADS result = check_standard(PyBytes_AsString(expected), PyBytes_Size(expected),
                                                   PyBytes_AsString(actual), PyBytes_Size(actual))
                                        ? Py_True
                                        : Py_False;
    Py_END_ALLOW_THREADS Py_DECREF(expected);
    Py_DECREF(actual);
    Py_INCREF(result);
    return result;
}

static PyMethodDef checker_methods[] = { { "standard", checker_standard, METH_VARARGS, "Standard DMOJ checker." },
                                         { NULL, NULL, 0, NULL } };

static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT, "_checker", NULL, -1, checker_methods, NULL, NULL, NULL, NULL
};

PyMODINIT_FUNC PyInit__checker(void) {
    return PyModule_Create(&moduledef);
}
