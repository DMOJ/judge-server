from __future__ import print_function
import sys

A = int(sys.argv[1])
B = int(sys.argv[2])
print(A, B)
print(A + B, file=sys.stderr)
