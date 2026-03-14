import re

import yaml.reader

if yaml.reader.Reader.NON_PRINTABLE.pattern == '[^\t\n\r -~\x85\xa0-\ud7ff\ue000-\ufffd]':
    yaml.reader.Reader.NON_PRINTABLE = re.compile(
        '[^\x09\x0a\x0d\x20-\x7e\x85\xa0-\ud7ff\ue000-\ufffd\U00010000-\U0010ffff]'
    )
