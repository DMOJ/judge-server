import os
import re


class NullStdoutMixin:
    """
    Some compilers print a lot of debug info to stdout even with successful compiles. This mixin pipes that generally-
    useless data into os.devnull so that the user never sees it.
    """

    def __init__(self, *args, **kwargs):
        self._devnull = open(os.devnull, 'w')
        super().__init__(*args, **kwargs)

    def cleanup(self):
        if hasattr(self, '_devnull'):
            self._devnull.close()
        super().cleanup()

    def get_compile_popen_kwargs(self):
        result = super().get_compile_popen_kwargs()
        result['stdout'] = self._devnull
        return result


class SingleDigitVersionMixin:
    version_regex = re.compile(r'.*?(\d+(?:\.\d+)*)', re.DOTALL)


class StripCarriageReturnsMixin:
    def create_files(self, problem_id, source_code, *args, **kwargs):
        source_code = source_code.replace(b'\r\n', b'\r').replace(b'\r', b'\n')
        super().create_files(problem_id, source_code, *args, **kwargs)
