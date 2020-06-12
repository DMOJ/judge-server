import os
import re
from shutil import copyfile

from dmoj.error import CompileError
from dmoj.executors.JAVA8 import Executor as JavaExecutor
from dmoj.utils.unicode import utf8text

recomment = re.compile(r'/\*.*?\*/', re.DOTALL | re.U)
resetup = re.compile(r'\bvoid\s+setup\s*\(\s*\)', re.U)

PAPPLET_SOURCE = os.path.join(os.path.dirname(__file__), 'processing', 'PApplet.jar')

template = b'''\
import java.math.*;
import java.util.*;

public class App extends PApplet {
    {code}

    public static void main(String[] args) {
        new App().setup();
    }
}
'''


class Executor(JavaExecutor):
    name = 'PDE'

    test_program = '''\
void setup() {
    println(readLine());
}'''

    def __init__(self, problem_id, source_code, **kwargs):
        if resetup.search(recomment.sub('', utf8text(source_code))) is None:
            raise CompileError('You must implement "void setup()"\n')

        code = template.replace(b'{code}', source_code)
        super(Executor, self).__init__(problem_id, code, **kwargs)

    def create_files(self, problem_id, source_code, *args, **kwargs):
        self._papplet_file = self._file('PApplet.jar')
        copyfile(PAPPLET_SOURCE, self._papplet_file)

        code = template.replace(b'{code}', source_code)
        super(Executor, self).create_files(problem_id, code, *args, **kwargs)

    def get_cmdline(self, **kwargs):
        # must inject the class path before the class name,
        # otherwise it gets treated as an command line argument
        cmdline = super(Executor, self).get_cmdline(**kwargs)
        return cmdline[:-1] + ['-cp', self._papplet_file] + cmdline[-1:]

    def get_compile_args(self):
        return super(Executor, self).get_compile_args() + ['-cp', self._papplet_file]

    @classmethod
    def get_runtime_versions(cls):
        return ('pde', (3, 5, 3)),
