import abc


class ExecutorMeta(abc.ABCMeta):
    """This metaclass treats class attributes that are annotated but never assigned as abstract.

    For example:
    >>> class Example(ExecutorMeta):
    ...     x: int
    would be an abstract class unless `x` is implemented.

    This means that when instantiating, an exception will be raised:
    >>> Example()
    TypeError: Can't instantiate abstract class Example with abstract methods x
    """

    def __new__(mcs, *args, **kwargs):
        cls = super().__new__(mcs, *args, **kwargs)
        cls.__abstractmethods__ |= {a for a in getattr(cls, '__annotations__', {}).keys() if not hasattr(cls, a)}
        return cls
