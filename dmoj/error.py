from dmoj.utils.unicode import utf8text


class CompileError(Exception):
    def __init__(self, message):
        super().__init__(utf8text(message, 'replace'))

    @property
    def message(self) -> str:
        return self.args[0]


class InternalError(Exception):
    pass


class OutputLimitExceeded(Exception):
    def __init__(self, stream, limit):
        super().__init__('exceeded %d-byte limit on %s stream' % (limit, stream))


class InvalidCommandException(Exception):
    def __init__(self, message=None):
        self.message = message
