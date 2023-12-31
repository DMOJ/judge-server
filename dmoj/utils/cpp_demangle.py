from ctypes import CDLL, POINTER, byref, c_char_p, c_int, c_size_t, c_void_p, string_at
from ctypes.util import find_library
from typing import Any

__all__ = ['demangle']

libc = CDLL(find_library('c'))

libstdcxx_path = find_library('stdc++')
libcxx_path = find_library('c++')

libstdcxx: Any = None if libstdcxx_path is None else CDLL(libstdcxx_path)
libcxx: Any = None if libcxx_path is None else CDLL(libcxx_path)

# Signature: char *__cxa_demangle(const char *mangled_name, char *output_buffer, size_t *length, int *status)
try:
    __cxa_demangle = libstdcxx.__cxa_demangle
except AttributeError:
    __cxa_demangle = libcxx.__cxa_demangle

__cxa_demangle.argtypes = [c_char_p, c_char_p, POINTER(c_size_t), POINTER(c_int)]
__cxa_demangle.restype = c_void_p

# Signature: void free(void *ptr)
free = libc.free
free.argtypes = [c_void_p]
free.restype = None


def demangle(name: bytes) -> bytes:
    status = c_int()
    result = __cxa_demangle(name, None, None, byref(status))

    if result:
        value = string_at(result)
        free(result)
        return value

    if status.value == -1:
        # Memory allocation failure
        raise MemoryError()
    elif status.value == -2:
        # `mangled_name` is not a valid mangled name
        return name
    elif status.value == -3:
        # Invalid argument
        raise RuntimeError('__cxa_demangle reported invalid argument')
    else:
        raise RuntimeError(f'unknown return value {status.value} from __cxa_demangle')
