# Based off https://github.com/django/django/blob/main/django/utils/functional.py, licensed under 3-clause BSD.
from functools import total_ordering

from dmoj.cptbox._cptbox import BufferProxy

_SENTINEL = object()


@total_ordering
class LazyBytes(BufferProxy):
    """
    Encapsulate a function call and act as a proxy for methods that are
    called on the result of that function. The function is not evaluated
    until one of the methods on the result is called.
    """

    def __init__(self, func):
        self.__func = func
        self.__value = _SENTINEL

    def __get_value(self):
        if self.__value is _SENTINEL:
            self.__value = self.__func()
        return self.__value

    @classmethod
    def _create_promise(cls, method_name):
        # Builds a wrapper around some magic method
        def wrapper(self, *args, **kw):
            # Automatically triggers the evaluation of a lazy value and
            # applies the given magic method of the result type.
            res = self.__get_value()
            return getattr(res, method_name)(*args, **kw)

        return wrapper

    def __cast(self):
        return bytes(self.__get_value())

    def _get_real_buffer(self):
        return self.__cast()

    def __bytes__(self):
        return self.__cast()

    def __repr__(self):
        return repr(self.__cast())

    def __str__(self):
        return str(self.__cast())

    def __eq__(self, other):
        if isinstance(other, LazyBytes):
            other = other.__cast()
        return self.__cast() == other

    def __lt__(self, other):
        if isinstance(other, LazyBytes):
            other = other.__cast()
        return self.__cast() < other

    def __hash__(self):
        return hash(self.__cast())

    def __mod__(self, rhs):
        return self.__cast() % rhs

    def __add__(self, other):
        return self.__cast() + other

    def __radd__(self, other):
        return other + self.__cast()

    def __deepcopy__(self, memo):
        # Instances of this class are effectively immutable. It's just a
        # collection of functions. So we don't need to do anything
        # complicated for copying.
        memo[id(self)] = self
        return self


for type_ in bytes.mro():
    for method_name in type_.__dict__:
        # All __promise__ return the same wrapper method, they
        # look up the correct implementation when called.
        if hasattr(LazyBytes, method_name):
            continue
        setattr(LazyBytes, method_name, LazyBytes._create_promise(method_name))
