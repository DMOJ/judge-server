from cptbox import SecurePopen, CHROOTSecurity

from .resource_proxy import ResourceProxy
from judgeenv import env

RUBY_FS = ['usr/bin/ruby', '.*\.[so|rb]']


class Executor(ResourceProxy):
    def __init__(self, problem_id, source_code):
        super(ResourceProxy, self).__init__()
        source_code_file = str(problem_id) + '.rb'
        with open(source_code_file, 'wb') as fo:
            fo.write(source_code)
        self._files = [source_code_file]

    def launch(self, *args, **kwargs):
        return SecurePopen(['ruby', self._files[0]] + list(args),
                           executable=env['runtime']['ruby'],
                           security=CHROOTSecurity(RUBY_FS),
                           time=kwargs.get('time'),
                           memory=kwargs.get('memory'))
