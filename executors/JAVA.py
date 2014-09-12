import os
import subprocess
from error import CompileError

try:
    from executors import ResourceProxy
except:
    pass
from ptbox import sandbox
from ptbox.chroot import CHROOTProcessDebugger

JAVA_FS = ["/usr/bin/java", ".*\.[so|jar]"]


class Executor(ResourceProxy):
    def __init__(self, env, problem_id, source_code):
        super(ResourceProxy).__init__()
        self.env = env
        source_code_file = problem_id + ".java"
        with open(source_code_file, "wb") as fo:
            fo.write(source_code)
        output_file = problem_id + ".class"
        javac_args = [env["javac"], source_code_file]
        javac_process = subprocess.Popen(javac_args, stderr=subprocess.PIPE)
        _, compile_error = javac_process.communicate()
        if javac_process.returncode != 0:
            os.unlink(source_code_file)
            raise CompileError(compile_error)
        self._files = [source_code_file, output_file]

    def launch(self, *args, **kwargs):
        return sandbox.execute(
            [self.env["java"], "-Djava.security.manager", "-client", "-Xmx%sK" % kwargs.get("memory"), "-cp", ".",
             self._files[1]] + list(args),
            time=kwargs.get("time"))