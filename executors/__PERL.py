def generate(env, name, source_code):
    source_code_file = str(name) + ".pl"
    with open(source_code_file, "wb") as fo:
        fo.write(source_code)
    return [source_code_file]

def launch(env, execute, generated_files, *args, **kwargs):
    return execute([env["perl"], generated_files[0]] + list(args), kwargs.get("time"), kwargs.get("memory"))
