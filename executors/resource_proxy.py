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