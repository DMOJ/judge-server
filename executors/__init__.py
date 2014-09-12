import os
import CPP
import CPP11
import JAVA
import PY2
import PY3
import RUBY


class ResourceProxy(object):
    def __init__(self):
        self._files = []

    def cleanup(self):
        for path in self._files:
            os.unlink(path)

    def launch(self, *args, **kwargs):
        pass

    def __del__(self):
        self.cleanup()