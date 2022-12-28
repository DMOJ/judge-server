from typing import Dict, List, Optional, Set

from dmoj.executors.asm_executor import ASMExecutor, NativeMixin


class Executor(NativeMixin, ASMExecutor):
    as_name = 'llc'
    optimize = 2

    test_program = """
declare i32 @getchar() nounwind
declare i32 @putchar(i32) nounwind

define i32 @main() {
  br label %start

start:
  %ch = call i32 @getchar()
  %cond = icmp ne i32 %ch, -1
  br i1 %cond, label %write, label %end

write:
  call i32 @putchar(i32 %ch)
  br label %start

end:
  ret i32 0
}
"""

    def find_features(self, source_code: bytes) -> Set[str]:
        return super().find_features(source_code) | {'libc'}

    def get_as_args(self, obj_file: str) -> List[str]:
        assert self._code is not None
        return [self.get_as_path(), '-filetype=obj', f'-O{self.optimize}', self._code, '-o', obj_file]

    @classmethod
    def get_version_flags(cls, command: str) -> List[str]:
        return ['-version'] if command == cls.as_name else super().get_version_flags(command)

    @classmethod
    def get_find_first_mapping(cls) -> Optional[Dict[str, List[str]]]:
        if cls.platform_prefixes is None:
            return None
        return {cls.ld_name: [f'{i}-ld' for i in cls.platform_prefixes] + ['ld'], 'llc': ['llc']}
