from typing import List, Optional, TYPE_CHECKING, Tuple

from dmoj.utils.error import print_protection_fault
from dmoj.utils.os_ext import strsignal
from dmoj.utils.unicode import utf8text

if TYPE_CHECKING:
    from dmoj.cptbox import TracedPopen
    from dmoj.executors.base_executor import BaseExecutor
    from dmoj.problem import TestCase


class Result:
    AC = 0
    WA = 1 << 0
    RTE = 1 << 1
    TLE = 1 << 2
    MLE = 1 << 3
    IR = 1 << 4
    SC = 1 << 5
    OLE = 1 << 6
    IE = 1 << 30
    COLORS_BYID = {
        'AC': 'green',
        'WA': 'red',
        'RTE': 'yellow',
        'TLE': 'white',
        'MLE': 'yellow',
        'IR': 'yellow',
        'SC': 'magenta',
        'OLE': 'yellow',
        'IE': 'red',
    }
    CODE_DISPLAY_ORDER = ('IE', 'TLE', 'MLE', 'OLE', 'RTE', 'IR', 'WA', 'SC')

    def __init__(
        self,
        case: 'TestCase',
        result_flag: int = 0,
        execution_time: float = 0,
        wall_clock_time: float = 0,
        max_memory: int = 0,
        context_switches: Tuple[int, int] = (0, 0),
        runtime_version: str = '',
        proc_output: bytes = b'',
        feedback: str = '',
        extended_feedback: str = '',
        points: float = 0,
    ):
        self.case: 'TestCase' = case
        self.result_flag: int = result_flag
        self.execution_time: float = execution_time
        self.wall_clock_time: float = wall_clock_time
        self.context_switches: Tuple[int, int] = context_switches
        self.runtime_version: str = runtime_version
        self.max_memory: int = max_memory
        self.proc_output: bytes = proc_output
        self.feedback: str = feedback
        self.extended_feedback: str = extended_feedback
        self.points: float = points

    def get_main_code(self) -> int:
        for flag in Result.CODE_DISPLAY_ORDER:
            code = getattr(Result, flag)
            if self.result_flag & code:
                return code
        return Result.AC

    def readable_codes(self) -> List[str]:
        execution_verdict = []
        for flag in Result.CODE_DISPLAY_ORDER:
            if self.result_flag & getattr(Result, flag):
                execution_verdict.append(flag)
        return execution_verdict or ['AC']

    @property
    def total_points(self) -> float:
        return self.case.points

    @property
    def output(self) -> str:
        return utf8text(self.proc_output[: self.case.output_prefix_length], 'replace')

    @classmethod
    def get_feedback_str(cls, error: bytes, process: 'TracedPopen', binary: 'BaseExecutor') -> str:
        is_ir_or_rte = (process.is_ir or process.is_rte) and not (process.is_tle or process.is_mle or process.is_ole)
        if hasattr(process, 'feedback'):
            feedback = utf8text(process.feedback)
        elif is_ir_or_rte:
            feedback = binary.parse_feedback_from_stderr(error, process)
        else:
            feedback = ''

        if not feedback and is_ir_or_rte:
            if not process.was_initialized or (error and b'error while loading shared libraries' in error):
                # Process may failed to initialize, resulting in a SIGKILL without any prior signals.
                # See <https://github.com/DMOJ/judge/issues/179> for more details.
                feedback = 'failed initializing'
            elif process.signal:
                feedback = strsignal(process.signal).lower()

        if process.protection_fault:
            syscall, callname, args, update_errno = process.protection_fault
            print_protection_fault(process.protection_fault)
            callname = callname.replace('sys_', '', 1)
            message = f'{callname} syscall disallowed'
            feedback = message

        return feedback

    def update_feedback(
        self, error: bytes, process: 'TracedPopen', binary: 'BaseExecutor', feedback: Optional[str] = None
    ) -> None:
        self.feedback = feedback or self.get_feedback_str(error, process, binary)


class CheckerResult:
    def __init__(
        self, passed: bool, points: float, feedback: Optional[str] = None, extended_feedback: Optional[str] = None
    ):
        # Make sure we don't kill the site bridge
        assert isinstance(passed, bool)
        assert isinstance(points, int) or isinstance(points, float)
        assert feedback is None or isinstance(feedback, str)
        assert extended_feedback is None or isinstance(extended_feedback, str)

        self.passed: bool = passed
        self.points: float = points
        self.feedback: Optional[str] = feedback
        self.extended_feedback: Optional[str] = extended_feedback
