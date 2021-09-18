import re

from termcolor import colored


def strip_ansi(s: str) -> str:
    # http://stackoverflow.com/questions/13506033/filtering-out-ansi-escape-sequences
    return re.sub(r'\x1b\[([0-9,A-Z]{1,2}(;[0-9]{1,2})?(;[0-9]{3})?)?[m|K]?', '', s)


def ansi_style(text: str) -> str:
    from dmoj.judgeenv import no_ansi

    def format_inline(text, attrs):
        data = attrs.split('|')
        colors = data[0].split(',')
        if not colors[0]:
            colors[0] = None
        attrs = data[1].split(',') if len(data) > 1 else []
        return colored(text, *colors, attrs=attrs)

    return re.sub(
        r'#ansi\[(.*?)\]\((.*?)\)', lambda x: format_inline(x.group(1), x.group(2)) if not no_ansi else x.group(1), text
    )


def print_ansi(*args, **kwargs) -> None:
    print(*map(ansi_style, args), **kwargs)
