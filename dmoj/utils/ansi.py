from collections import OrderedDict
import re

try:
    import ansi2html

    def format_ansi(s):
        return ansi2html.Ansi2HTMLConverter(inline=True).convert(s, full=False)
except ImportError:
    def format_ansi(s):
        escape = OrderedDict([
            ('&', '&amp;'),
            ('<', '&lt;'),
            ('>', '&gt;'),
        ])
        for a, b in escape.items():
            s = s.replace(a, b)

        # http://stackoverflow.com/questions/13506033/filtering-out-ansi-escape-sequences
        return re.sub(r'\x1b\[([0-9,A-Z]{1,2}(;[0-9]{1,2})?(;[0-9]{3})?)?[m|K]?', '', s)
