import re

import yaml.reader

if yaml.reader.Reader.NON_PRINTABLE.pattern == '[^\t\n\r -~\x85\xa0-\ud7ff\ue000-\ufffd]':
    # `NON_PRINTABLE` is declared `Final[Pattern[str]]` in python/typeshed@6fba3ae
    yaml.reader.Reader.NON_PRINTABLE = re.compile(  # type: ignore[misc]
        '[^\x09\x0a\x0d\x20-\x7e\x85\xa0-\ud7ff\ue000-\ufffd\U00010000-\U0010ffff]'
    )
