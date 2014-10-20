from judgeenv import env
from .GCCExecutor import make_executor

Executor, initialize = make_executor('F95', 'gfortran', [], '.f95', '''\
PRINT *, "Hello, World!"
END''')

del make_executor, env
