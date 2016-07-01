from dmoj.judgeenv import env
from .GCCExecutor import GCCExecutor


class Executor(GCCExecutor):
    name = 'F95'
    command = 'gfortran'
    ext = '.f95'
    test_program = '''\
character(100) :: line
read(*,'(A)') line
write(*,'(A)') line
end
'''
