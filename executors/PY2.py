from ptbox.chroot import CHROOTProcessDebugger

PYTHON_FS = ["usr/bin/python", ".*\.[so|py]", "/usr/lib/python", "/etc/.*"]


def generate(env, name, source_code):
    source_code_file = str(name) + ".py"
    with open(source_code_file, "wb") as fo:
        fo.write(source_code)
    return [source_code_file]


def launch(env, execute, generated_files, *args, **kwargs):
    return execute([env["python"], "-B", generated_files[0]] + list(args),
                   debugger=CHROOTProcessDebugger(filesystem=PYTHON_FS), time=kwargs.get("time"),
                   memory=kwargs.get("memory"))
