# type: ignore
import sys

# Drop to Python's limit, see https://github.com/python/cpython/issues/95778
INT_MAX_NUMBER_DIGITS = getattr(sys.int_info, 'default_max_str_digits', 4300)
int_ = int

if isinstance(__builtins__, dict):
    builtins = __builtins__
else:
    builtins = __builtins__.__dict__


class patched_int_meta(type):
    def __instancecheck__(self, instance):
        return isinstance(instance, int_)

    def __subclasscheck__(cls, subclass):
        return issubclass(subclass, int_)

    def __eq__(self, other):
        return self is other or other is int_

    def __hash__(self):
        return hash(int_)


class patched_int(int_, metaclass=patched_int_meta):
    def __new__(cls, s=0, *args, **kwargs):
        if isinstance(s, str) and len(s) > INT_MAX_NUMBER_DIGITS:
            raise ValueError('integer is too long')
        if cls is patched_int:
            cls = int_
        return int_.__new__(cls, s, *args, **kwargs)


def apply():
    builtins['int'], builtins['int_'] = patched_int, int_


def unapply():
    builtins['int'] = int_
