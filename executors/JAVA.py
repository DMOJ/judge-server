import subprocess
from __init__ import CompileError

def generate(env, class_name, source_code):
    source_code_file = class_name + ".java"
    with open(source_code_file, "wb") as fo:
        fo.write(source_code)
    output_file = class_name + ".class"
    javac_args = [env['javac'], source_code_file]
    javac_process = subprocess.Popen(javac_args, stderr=subprocess.PIPE)
    _, compile_error = javac_process.communicate()
    if javac_process.returncode != 0:
        raise CompileError(compile_error, source_code_file)
    return [source_code_file, output_file], \
           [env['java'],
            "-Djava.security.manager",
            # "-Xmx" TODO
            "-cp", ".", class_name]
