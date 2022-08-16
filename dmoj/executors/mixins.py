import re

class SingleDigitVersionMixin:
    version_regex = re.compile(r'.*?(\d+(?:\.\d+)*)', re.DOTALL)


class StripCarriageReturnsMixin:
    def create_files(self, problem_id, source_code, *args, **kwargs):
        source_code = source_code.replace(b'\r\n', b'\r').replace(b'\r', b'\n')
        super().create_files(problem_id, source_code, *args, **kwargs)
