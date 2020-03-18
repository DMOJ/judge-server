import re
import sys

import yaml.reader

if yaml.reader.Reader.NON_PRINTABLE.pattern == u'[^\t\n\r -~\x85\xa0-\ud7ff\ue000-\ufffd]' and sys.maxunicode > 65535:
    yaml.reader.Reader.NON_PRINTABLE = re.compile(
        u'[^\x09\x0A\x0D\x20-\x7E\x85\xA0-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]')
