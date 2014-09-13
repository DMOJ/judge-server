import os
import subprocess
import sys
from error import CompileError
from .resource_proxy import ResourceProxy
from ptbox import sandbox
from ptbox.chroot import CHROOTProcessDebugger

C_FS = [".*\.[so]"]


class Executor(ResourceProxy):
    def __init__(self, env, problem_id, source_code):
        super(ResourceProxy).__init__()
        self.env = env
        source_code_file = str(problem_id) + ".cpp"
        with open(source_code_file, "wb") as fo:
            fo.write(source_code)
        if sys.platform == "win32":
            compiled_extension = ".exe"
            linker_options = ["-Wl,--stack,8388608", "-static"]
        else:
            compiled_extension = ""
            linker_options = []
        output_file = str(problem_id) + compiled_extension
        gcc_args = [env["gcc"], source_code_file, "-O2", "-std=c++0x"] + linker_options + ["-s", "-o", output_file]
        gcc_process = subprocess.Popen(gcc_args, stderr=subprocess.PIPE)
        _, compile_error = gcc_process.communicate()
        if gcc_process.returncode != 0:
            os.unlink(source_code_file)
            raise CompileError(compile_error)
        self._files = [source_code_file, output_file]

    def launch(self, *args, **kwargs):
        return sandbox.execute(["./" + self._files[1]] + list(args), CHROOTProcessDebugger(filesystem=C_FS),
                           kwargs.get("time"),
                           kwargs.get("memory"))