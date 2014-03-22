import subprocess
import sys

class Cpp11CompileError(Exception):
    pass


def generate(compiler, name, source_code):
    source_code_file = str(name) + ".cpp"
    with open(source_code_file, "wb") as fo:
        fo.write(source_code)
    if sys.platform == "win32":
        compiled_extension = ".exe"
        linker_options = ["-Wl,--stack,8388608", "-static"]
    else:
        compiled_extension = ""
        linker_options = []
    output_file = str(name) + compiled_extension
    gcc_args = [compiler, source_code_file, "-O2", "-std=c++0x"] + linker_options + ["-s", "-o", output_file]
    gcc_process = subprocess.Popen(gcc_args, stderr=subprocess.PIPE)
    _, compile_error = gcc_process.communicate()
    if gcc_process.returncode != 0:
        raise CppCompileError(compile_error, source_code_file)
    return [source_code_file, output_file], ["./" + output_file]
