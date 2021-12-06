from dmoj.executors.compiled_executor import CompiledExecutor


class Executor(CompiledExecutor):
    ext = 'i'
    command = 'ick'
    test_program = """\
        PLEASE DO ,1 <- #1
        DO .4 <- #0
        DO .5 <- #0
        DO COME FROM (30)
        DO WRITE IN ,1
        DO .1 <- ,1SUB#1
        DO (10) NEXT
        PLEASE GIVE UP
(20)    PLEASE RESUME '?.1$#256'~'#256$#256'
(10)    DO (20) NEXT
        DO FORGET #1
        PLEASE DO .2 <- .4
        DO (1000) NEXT
        DO .4 <- .3~#255
        PLEASE DO .3 <- !3~#15'$!3~#240'
        DO .3 <- !3~#15'$!3~#240'
        DO .2 <- !3~#15'$!3~#240'
        PLEASE DO .1 <- .5
        DO (1010) NEXT
        DO .5 <- .2
        DO ,1SUB#1 <- .3
(30)    PLEASE READ OUT ,1
"""

    def get_compile_args(self):
        flags = [self.get_command(), '-O', self._code]
        if self.problem == self.test_name:
            # Do not fail self-test to random compiler bug.
            flags.insert(1, '-b')
        return flags
