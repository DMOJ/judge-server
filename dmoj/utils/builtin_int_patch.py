# type: ignore

INT_MAX_NUMBER_DIGITS = 10000


class patched_int_meta(type):
    def __subclasscheck__(cls, subclass):
        return issubclass(subclass, bool) or super().__subclasscheck__(subclass)


int_ = int


class patched_int(int_, metaclass=patched_int_meta):
    def __new__(self, s, *args, **kwargs):
        if isinstance(s, str) and len(s) > INT_MAX_NUMBER_DIGITS:
            raise ValueError('integer is too long')
        return int_(s, *args, **kwargs)


__builtins__.int, __builtins__.int_ = patched_int, int
