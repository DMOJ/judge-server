import six


class CompileError(Exception):
    def __init__(self, message):
        if isinstance(message, six.binary_type):
            message = message.decode('utf-8')
        super(CompileError, self).__init__(message)


class InternalError(Exception):
    pass
