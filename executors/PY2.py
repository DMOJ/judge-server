from ptbox.chroot import CHROOTProcessDebugger

PYTHON_FS = ["usr/bin/python", ".*\.[so|py]", ".*/lib(?:32|64)?/python[\d.]+/.*", ".*/lib/locale/.*"]


def generate(env, name, source_code):
    source_code_file = str(name) + ".py"
    customize = '''__import__("sys").stdout = __import__("os").fdopen(1, 'w', 65536)
__import__("sys").stdin = __import__("os").fdopen(0, 'r', 65536)
'''
    with open(source_code_file, "wb") as fo:
        fo.write(customize)
        fo.write(source_code)
    return [source_code_file]


def launch(env, execute, generated_files, *args, **kwargs):
    return execute([env["python"], "-B", generated_files[0]] + list(args),
                   debugger=CHROOTProcessDebugger(filesystem=PYTHON_FS), time=kwargs.get("time"),
                   memory=kwargs.get("memory"))
