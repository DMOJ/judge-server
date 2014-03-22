def generate(interpreter, name, source_code):
    source_code_file = str(name) + ".py"
    with open(source_code_file, "wb") as fo:
        fo.write(source_code)
    return [source_code_file], [interpreter, source_code_file]
