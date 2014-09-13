import os

from .resource_proxy import ResourceProxy
from ptbox import sandbox
from ptbox.chroot import CHROOTProcessDebugger

RUBY_FS = ["usr/bin/ruby", ".*\.[so|rb]"]


class Executor(ResourceProxy):
    def __init__(self, env, problem_id, source_code):
        super(ResourceProxy).__init__()
        self.env = env
        source_code_file = str(problem_id) + ".rb"
        with open(source_code_file, "wb") as fo:
            fo.write(source_code)
        self._files = [source_code_file]

    def launch(self, *args, **kwargs):
        return sandbox.execute([self.env["ruby"], self._files[0]] + list(args),
                               debugger=CHROOTProcessDebugger(filesystem=RUBY_FS), time=kwargs.get("time"),
                               memory=kwargs.get("memory"))
