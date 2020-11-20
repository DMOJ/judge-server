from typing import cast

from dmoj.cli import LocalPacketManager
from dmoj.judge import Judge
from dmoj.packet import PacketManager
from dmoj.result import Result


class ApiPacketManager(LocalPacketManager):
    def __init__(self, judge, cache):
        self.cache = cache
        self.judge = judge

    def test_case_status_packet(self, position: int, result: Result):
        pass

    def update_submission(self, data: dict):
        result = self.cache.get(self.judge.current_submission.id)
        result = result or {}
        result.update(data)
        self.cache.set(self.judge.current_submission.id, result, 60 * 30)

    def compile_error_packet(self, log):
        self.update_submission({'log': log, 'status': Result.RTE})

    def compile_message_packet(self, log):
        self.update_submission({'log': log})

    def internal_error_packet(self, message):
        self.update_submission({'status': Result.IE, 'message': message})

    def grading_end_packet(self):
        # TODO 该保存判题结果的哪些信息。
        self.update_submission({})


class ApiJudge(Judge):
    def __init__(self, cache):
        super().__init__(cast(PacketManager, ApiPacketManager(self, cache)))
        self.submission_id_counter = 0
        self.graded_submissions = []
