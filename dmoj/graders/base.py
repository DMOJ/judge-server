import six


class BaseGrader(object):
    def __init__(self, judge, problem, language, source):
        if isinstance(source, six.text_type):
            source = source.encode('utf-8')
        self.source = source
        self.language = language
        self.problem = problem
        self.judge = judge
        self.binary = self._generate_binary()
        self._terminate_grading = False
        self._current_proc = None

    def grade(self, case):
        raise NotImplementedError

    def _generate_binary(self):
        raise NotImplementedError

    def terminate_grading(self):
        self._terminate_grading = True
        if self._current_proc:
            try:
                self._current_proc.kill()
            except OSError:
                pass
        pass
