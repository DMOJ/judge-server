import codecs
import os
import sys

import six
from six import __init__


def utf8bytes(maybe_text):
    if maybe_text is None:
        return
    if isinstance(maybe_text, six.binary_type):
        return maybe_text
    return maybe_text.encode('utf-8')


def utf8text(maybe_bytes, errors='strict'):
    if maybe_bytes is None:
        return
    if isinstance(maybe_bytes, six.text_type):
        return maybe_bytes
    return maybe_bytes.decode('utf-8', errors)


def unicode_stdout_stderr():
    if six.PY2:
        sys.stdout = codecs.getwriter('utf-8')(os.fdopen(sys.stdout.fileno(), 'w', 0))
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr)
    else:
        sys.stdout = codecs.getwriter('utf-8')(open(sys.stdout.fileno(), 'wb', 0, closefd=False))
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())