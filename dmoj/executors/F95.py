from .gcc_executor import GCCExecutor


class Executor(GCCExecutor):
    command = 'gfortran'
    ext = 'f95'
    test_program = """\
character(100) :: line
read(*,'(A)') line
write(*,'(A)') line
end
"""
