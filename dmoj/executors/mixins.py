import os


class NullStdoutMixin(object):
    def __init__(self, *args, **kwargs):
        self._devnull = open(os.devnull, 'w')
        super(NullStdoutMixin, self).__init__(*args, **kwargs)

    def cleanup(self):
        if hasattr(self, '_devnull'):
            self._devnull.close()
        super(NullStdoutMixin, self).cleanup()

    def get_compile_popen_kwargs(self):
        result = super(NullStdoutMixin, self).get_compile_popen_kwargs()
        result['stdout'] = self.devnull
        return result
