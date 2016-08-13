import sys

a, b = [
    ('a', 'b'),
    ('a', 'a'),
    ('a', 'a '),
    ('a', 'a\n'),
    ('a', 'a\n  b'),
    ('a', 'a\n \n b'),
    ('a\nb', 'a\n \n b'),
    ('a b', 'a\nb'),
    ('a   b', 'a \n b'),
    ('a   \bb', 'a \n b'),
    ('a   \nb', 'a \n b'),
    ('    a   k z  zz  \nb', 'a k z zz\n        b'),
    ('\n\n  Hello,      World!   ', 'Hello, World!'),
][int(raw_input()) - 1]

print >>sys.stderr, a
print >>sys.stdout, b