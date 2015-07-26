import _checker
assert _checker.standard('a', 'b') == False
assert _checker.standard('a', 'a') == True
assert _checker.standard('a', 'a ') == True
assert _checker.standard('a', 'a\n') == True
assert _checker.standard('a', 'a\n  b') == False
assert _checker.standard('a', 'a\n \n b') == False
assert _checker.standard('a\nb', 'a\n \n b') == True
assert _checker.standard('a b', 'a\nb') == False
assert _checker.standard('a   b', 'a \n b') == False
assert _checker.standard('a   \bb', 'a \n b') == False
assert _checker.standard('a   \nb', 'a \n b') == True
assert _checker.standard('    a   k z  zz  \nb', 'a k z zz\n        b') == True
assert _checker.standard('\n\n  Hello,      World!   ', 'Hello, World!') == True
