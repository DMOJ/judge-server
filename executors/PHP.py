def generate(env, name, source_code):
    source_code_file = str(name) + ".php"
    with open(source_code_file, "wb") as fo:
        fo.write(source_code)
    return [source_code_file], [env['php'], source_code_file]
