from ptbox import sandbox
from ptbox.chroot import CHROOTProcessDebugger

RUBY_FS = ["usr/bin/ruby", ".*\.[so|rb]"]

def generate(env, name, source_code):
    source_code_file = str(name) + ".rb"
    with open(source_code_file, "wb") as fo:
        fo.write(source_code)
    return [source_code_file]

def launch(env, generated_files, *args, **kwargs):
    return sandbox.execute([env["ruby"], generated_files[0]] + list(args),
                   debugger=CHROOTProcessDebugger(filesystem=RUBY_FS), time=kwargs.get("time"),
                   memory=kwargs.get("memory"))
