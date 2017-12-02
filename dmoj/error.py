from dmoj.utils.unicode import utf8text


class CompileError(Exception):
    def __init__(self, message):
        super(CompileError, self).__init__(utf8text(message, 'replace'))


class InternalError(Exception):
    pass
