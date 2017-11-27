from __future__ import print_function

import errno
import os
import shutil
import tempfile

from dmoj.judgeenv import env


class ResourceProxy(object):
    def __init__(self):
        self._dir = tempfile.mkdtemp(dir=env.tempdir)

    def cleanup(self):
        if not hasattr(self, '_dir'):
            # We are really toasted, as constructor failed.
            print('ResourceProxy error: not initialized?')
            return
        try:
            shutil.rmtree(self._dir)  # delete directory
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise

    def _file(self, *paths):
        return os.path.join(self._dir, *paths)

    def launch(self, *args, **kwargs):
        raise NotImplementedError()

    def launch_unsafe(self, *args, **kwargs):
        raise NotImplementedError()

    def __del__(self):
        self.cleanup()
