import codecs
import sys
from typing import Optional


def utf8bytes(maybe_text) -> Optional[bytes]:
    if maybe_text is None:
        return None
    if isinstance(maybe_text, bytes):
        return maybe_text
    return maybe_text.encode('utf-8')


def utf8text(maybe_bytes, errors='strict') -> Optional[str]:
    if maybe_bytes is None:
        return None
    if isinstance(maybe_bytes, str):
        return maybe_bytes
    return maybe_bytes.decode('utf-8', errors)


def unicode_stdout_stderr():
    sys.stdout = codecs.getwriter('utf-8')(open(sys.stdout.fileno(), 'wb', 0, closefd=False))
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
