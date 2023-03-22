import subprocess

from dmoj.config import ConfigNode, InvalidInitException
from dmoj.graders.standard import Grader as StandardGrader


class Grader(StandardGrader):
    def _launch_process(self, case):
        time_limit = case.config.time_limit or self.problem.time_limit
        if isinstance(time_limit, ConfigNode):
            time_limit = time_limit.get(self.language, self.problem.time_limit)
        if not isinstance(time_limit, (int, float)):
            raise InvalidInitException('Could not parse `time_limit` node')

        self._current_proc = self.binary.launch(
            time=time_limit,
            memory=self.problem.memory_limit,
            symlinks=case.config.symlinks,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            wall_time=case.config.wall_time_factor * time_limit,
        )
