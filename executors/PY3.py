import os
from cptbox import CHROOTSecurity, SecurePopen
from .resource_proxy import ResourceProxy

PYTHON_FS = ["/dev/urandom", ".*\.[so|py]", ".*/lib(?:32|64)?/python[\d.]+/.*",
             ".*/lib/locale/.*", '/usr/lib64', '.*/pyvenv.cfg', '/proc/meminfo']


class Executor(ResourceProxy):
    def __init__(self, env, problem_id, source_code):
        super(ResourceProxy, self).__init__()
        self.env = env
        source_code_file = str(problem_id) + ".py"
        customize = '''\
__import__("sys").stdout = __import__("os").fdopen(1, 'w', 65536)
__import__("sys").stdin = __import__("os").fdopen(0, 'r', 65536)
'''
        with open(source_code_file, "wb") as fo:
            fo.write(customize)
            fo.write(source_code)
        self._files = [source_code_file]

    def launch(self, *args, **kwargs):
        return SecurePopen(['python', '-BS', self._files[0]] + list(args),
                           executable=self.env['python3'],
                           security=CHROOTSecurity(PYTHON_FS + [str(self.env['python3dir']) + '.*', os.getcwd() + '$']),
                           time=kwargs.get('time'),
                           memory=kwargs.get('memory'),
                           address_grace=131072)