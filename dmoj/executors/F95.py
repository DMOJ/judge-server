from dmoj.executors.c_like_executor import CLikeExecutor, GCCMixin


class Executor(GCCMixin, CLikeExecutor):
    command = 'gfortran'
    ext = 'f95'
    std = 'f95'
    test_program = """\
character(100) :: line
read(*,'(A)') line
write(*,'(A)') line
end
"""
