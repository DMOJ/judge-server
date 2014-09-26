import os
import subprocess
from cptbox import SecurePopen, NullSecurity
from error import CompileError

from .resource_proxy import ResourceProxy
from judgeenv import env

JAVA_FS = ['/usr/bin/java', '.*\.[so|jar]']


class Executor(ResourceProxy):
    def __init__(self, problem_id, source_code):
        super(ResourceProxy, self).__init__()
        source_code_file = problem_id + '.java'
        with open(source_code_file, 'wb') as fo:
            fo.write(source_code)
        output_file = problem_id + '.class'
        javac_args = [env['runtime']['javac'], source_code_file]
        javac_process = subprocess.Popen(javac_args, stderr=subprocess.PIPE)
        _, compile_error = javac_process.communicate()
        self._files = [source_code_file, output_file]
        if javac_process.returncode != 0:
            os.unlink(source_code_file)
            raise CompileError(compile_error)

    def launch(self, *args, **kwargs):
        return SecurePopen(['java', '-Djava.security.manager', '-client',
                            '-Xmx%sK' % kwargs.get('memory'), '-cp', '.',
                                 self._files[1]] + list(args),
                           executable=env['runtime']['java'],
                           security=NullSecurity(),
                           time=kwargs.get('time'),
                           memory=kwargs.get('memory'))