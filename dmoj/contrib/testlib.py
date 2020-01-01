from dmoj.contrib.default import ContribModule as DefaultContribModule
from dmoj.error import InternalError
from dmoj.result import CheckerResult
from dmoj.utils.helper_files import parse_helper_file_error


class ContribModule(DefaultContribModule):
    AC = 0
    WA = 1
    PE = 2
    IE = 3

    name = 'testlib'

    @classmethod
    def parse_return_code(cls, proc, executor, point_value, time_limit, memory_limit, feedback, name, stderr):
        if proc.returncode == cls.AC:
            return CheckerResult(True, point_value, feedback=feedback)
        elif proc.returncode == cls.WA:
            return CheckerResult(False, 0, feedback=feedback)
        elif proc.returncode == cls.PE:
            return CheckerResult(False, 0, feedback=feedback or 'Presentation Error')
        elif proc.returncode == cls.IE:
            raise InternalError('%s failed assertion with message %s' % (name, feedback))
        else:
            parse_helper_file_error(proc, executor, name, stderr, time_limit, memory_limit)
