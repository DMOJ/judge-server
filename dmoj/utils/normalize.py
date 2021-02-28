from io import TextIOWrapper


def normalized_file_copy(src, dst, block_size=16384):
    src_wrap = TextIOWrapper(src, encoding='iso-8859-1', newline=None)
    dst_wrap = TextIOWrapper(dst, encoding='iso-8859-1', newline='')

    add_newline = False
    while True:
        buf = src_wrap.read(block_size)
        if not buf:
            break
        dst_wrap.write(buf)
        add_newline = not buf.endswith('\n')

    if add_newline:
        dst_wrap.write('\n')

    src_wrap.detach()
    dst_wrap.detach()
