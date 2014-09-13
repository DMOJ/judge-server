from cptbox import SecurePopen, CHROOTSecurity

from .resource_proxy import ResourceProxy

RUBY_FS = ["usr/bin/ruby", ".*\.[so|rb]"]


class Executor(ResourceProxy):
    def __init__(self, env, problem_id, source_code):
        super(ResourceProxy, self).__init__()
        self.env = env
        source_code_file = str(problem_id) + ".rb"
        with open(source_code_file, "wb") as fo:
            fo.write(source_code)
        self._files = [source_code_file]

    def launch(self, *args, **kwargs):
        return SecurePopen(['ruby', self._files[0]] + list(args),
                           executable=self.env['ruby'],
                           security=CHROOTSecurity(RUBY_FS),
                           time=kwargs.get('time'),
                           memory=kwargs.get('memory'))
