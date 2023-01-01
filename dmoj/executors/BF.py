from collections import defaultdict
from typing import DefaultDict, Dict, List, Optional, Tuple, Union

from dmoj.cptbox import TracedPopen
from dmoj.error import CompileError
from dmoj.executors.LLC import Executor as LLCExecutor


# This executor translates BF into LLVM and runs optimizations.
# If a BF program does not segfault, the optimized version should not segfault.
# If a BF program segfaults, the optimized version does not guarantee anything.
# Example 1: "[-<+>]" does not segfault.
# Example 2: "+[-<+>]" segfaults, and the optimized version segfaults too.
# Example 3: "+[-<+->]" segfaults, and the optimized version doesn't segfault.
#            The optimized version removed a load/store that causes segfault.
#
# The optimizing compiler is organized like this:
# 1. Python pass, to optimize simple loops
# 2. Python pass, to translate into LLVM
# 3. "opt" using custom passes
# 4. "llc" and "ld"
TEMPLATE = b"""
declare i64 @strtoll(i8*, i8**, i32) nounwind
declare i32 @getpagesize() nounwind
declare i8* @mmap(i8*, i64, i32, i32, i32, i64) nounwind
declare i32 @mprotect(i8*, i64, i32) nounwind
declare i32 @getchar_unlocked() nounwind
declare i32 @putchar_unlocked(i32) nounwind

define i32 @main(i32 %argc, i8** %argv) {
  %size0 = getelementptr i8*, i8** %argv, i64 1
  %size1 = load i8*, i8** %size0
  %size = call i64 @strtoll(i8* %size1, i8** null, i32 10)

  ; 2 page buffer
  %page32 = call i32 @getpagesize()
  %page64 = zext i32 %page32 to i64
  %page2 = add i64 %page64, %page64
  %mmapsize = add i64 %size, %page2

  ; mmap NULL size PROT_READ|PROT_WRITE MAP_PRIVATE|MAP_ANONYMOUS -1 0
  %p_before = call i8* @mmap(i8* null, i64 %mmapsize, i32 3, i32 34, i32 -1, i64 0)
  %pi = ptrtoint i8* %p_before to i64
  %pfail = icmp uge i64 %pi, -4095  ; -4095 to -1 indicates error
  br i1 %pfail, label %end2, label %prot0

prot0:
  %mp0 = call i32 @mprotect(i8* %p_before, i64 %page64, i32 0)  ; mprotect p_before page_size PROT_NONE
  %mb0 = icmp eq i32 %mp0, 0
  br i1 %mb0, label %prot1, label %end2

prot1:
  %p = getelementptr i8, i8* %p_before, i64 %page64
  %p_after = getelementptr i8, i8* %p, i64 %size
  %mp1 = call i32 @mprotect(i8* %p_after, i64 %page64, i32 0)  ; mprotect p_after page_size PROT_NONE
  %mb1 = icmp eq i32 %mp1, 0
  br i1 %mb1, label %bf, label %end2

bf:
  {code}
  ret i32 0

end2:
  ret i32 2
}
"""


# Helper for simple loops. Consider the loop "[>>++>-<<<-]".
# This helper translates it into [(2, 2), (3, -1)]. Later, the LLVM looks like this:
#   if (p[0] != 0) { p[2] += p[0] * 2; p[3] += p[0] * -1; p[0] = 0; }
# The if-guard is needed so that programs like "[-<+>]" don't segfault.
def simple_loop(bf_inst: List[Union[str, List[Tuple[int, int]]]]) -> Optional[List[Tuple[int, int]]]:
    loop: DefaultDict[int, int] = defaultdict(int)
    ptr = 0
    for c in bf_inst:
        assert c in ['>', '<', '+', '-']
        if c == '>':
            ptr += 1
        elif c == '<':
            ptr -= 1
        elif c == '+':
            loop[ptr] += 1
        elif c == '-':
            loop[ptr] -= 1
    if ptr != 0:
        return None
    if loop[0] != -1:
        return None
    loop.pop(0)
    return [(i, j) for i, j in loop.items() if j]


def compile_to_llvm(source_code: bytes) -> bytes:
    # Do a pass to optimize simple loops.
    # This speeds up the opt step, because opt takes a long time to optimize simple loops.
    bf_inst: List[Union[str, List[Tuple[int, int]]]] = []
    bf_stack: List[int] = []
    simple = True  # Indicates if current loop only uses ><+-
    for b in source_code:
        if b in b'><+-':
            bf_inst.append(chr(b))
        elif b in b',.':
            bf_inst.append(chr(b))
            simple = False
        elif b == b'['[0]:
            bf_inst.append('[')
            bf_stack.append(len(bf_inst))
            simple = True
        elif b == b']'[0]:
            if not bf_stack:
                raise CompileError(b'Unmatched brackets\n')
            i = bf_stack.pop()
            loop = simple_loop(bf_inst[i:]) if simple else None
            if loop is None:
                bf_inst.append(']')
            else:
                bf_inst[i - 1 :] = [loop]
            simple = False

    if bf_stack:
        raise CompileError(b'Unmatched brackets\n')

    inst: List[str] = []
    stack: List[Tuple[int, str]] = []
    head, label = '%p', '%bf'  # current %p and label

    for i, c in enumerate(bf_inst):
        if isinstance(c, list):
            if c:
                inst.append(f'%b{i} = load i8, i8* {head}')
                inst.append(f'%c{i} = icmp ne i8 %b{i}, 0')
                inst.append(f'br i1 %c{i}, label %x{i}, label %y{i}')
                inst.append(f'x{i}:')
                for v, n in c:
                    inst.append(f'%p{i}v{v} = getelementptr i8, i8* {head}, i64 {v}')
                    inst.append(f'%b{i}v{v} = load i8, i8* %p{i}v{v}')
                    inst.append(f'%c{i}v{v} = mul i8 %b{i}, {n}')
                    inst.append(f'%d{i}v{v} = add i8 %b{i}v{v}, %c{i}v{v}')
                    inst.append(f'store i8 %d{i}v{v}, i8* %p{i}v{v}')
                inst.append(f'store i8 0, i8* {head}')
                inst.append(f'br label %y{i}')
                inst.append(f'y{i}:')
                label = f'%y{i}'
            else:
                # Don't need if-guard for "[-]"
                inst.append(f'store i8 0, i8* {head}')
        elif c in '><':
            v = 1 if c == '>' else -1
            inst.append(f'%p{i} = getelementptr i8, i8* {head}, i64 {v}')
            head = f'%p{i}'
        elif c in '+-':
            v = 1 if c == '+' else -1
            inst.append(f'%b{i} = load i8, i8* {head}')
            inst.append(f'%c{i} = add i8 %b{i}, {v}')
            inst.append(f'store i8 %c{i}, i8* {head}')
        elif c == ',':
            inst.append(f'%b{i} = call i32 @getchar_unlocked()')
            inst.append(f'%c{i} = trunc i32 %b{i} to i8')
            inst.append(f'store i8 %c{i}, i8* {head}')
        elif c == '.':
            inst.append(f'%b{i} = load i8, i8* {head}')
            inst.append(f'%c{i} = zext i8 %b{i} to i32')
            inst.append(f'call i32 @putchar_unlocked(i32 %c{i})')
        elif c == '[':
            inst.append(f'br label %y{i}')
            inst.append(f'x{i}:')
            inst.append(f'%p{i}x = phi i8* [%p{i}y, %y{i}]')
            stack.append((i, f'[{head}, {label}]'))
            head, label = f'%p{i}x', f'%x{i}'
        elif c == ']':
            j, phi = stack.pop()
            inst.append(f'br label %y{j}')
            inst.append(f'y{j}:')
            inst.append(f'%p{j}y = phi i8* {phi}, [{head}, {label}]')
            inst.append(f'%b{j} = load i8, i8* %p{j}y')
            inst.append(f'%c{j} = icmp ne i8 %b{j}, 0')
            inst.append(f'br i1 %c{j}, label %x{j}, label %z{j}')
            inst.append(f'z{j}:')
            head, label = f'%p{j}y', f'%z{j}'

    assert not stack
    return TEMPLATE.replace(b'{code}', '\n'.join(inst).encode())


OPT_PASSES = [
    # Shorten instructions
    'instcombine',
    'gvn',
    # Optimize loops
    'loop-rotate',
    'loop-mssa(licm)',
    'indvars',
    # Clean up
    'simplifycfg',
    'instcombine',
    'gvn',
]


class Executor(LLCExecutor):
    test_program = ',+[-.,+]'
    opt_name = 'opt'

    def create_files(self, problem_id: str, source_code: bytes, *args, **kwargs) -> None:
        super().create_files(problem_id, compile_to_llvm(source_code), *args, **kwargs)

    def launch(self, *args, **kwargs) -> TracedPopen:
        memory = kwargs['memory']
        # For some reason, RLIMIT_DATA is being applied to our mmap, so we have to increase the memory limit.
        kwargs['memory'] += 8192
        return super().launch(str(memory * 1024), **kwargs)

    # Do both opt and llc.
    def assemble(self) -> Tuple[bytes, List[str]]:
        assert self._code is not None
        args = [self.runtime_dict[self.opt_name], '-S', f'-passes={",".join(OPT_PASSES)}', self._code, '-o', self._code]
        process = self.create_compile_process(args)
        opt_output = self.get_compile_output(process)
        as_output, to_link = super().assemble()
        return b'\n'.join(filter(None, [opt_output, as_output])), to_link

    @classmethod
    def get_versionable_commands(cls) -> List[Tuple[str, str]]:
        return [(cls.opt_name, cls.runtime_dict[cls.opt_name])] + super().get_versionable_commands()

    @classmethod
    def get_find_first_mapping(cls) -> Optional[Dict[str, List[str]]]:
        res = super().get_find_first_mapping()
        if res is None:
            return None
        res[cls.opt_name] = [cls.opt_name]
        return res
