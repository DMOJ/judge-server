from http.server import BaseHTTPRequestHandler
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from dmoj.judge import Judge


class JudgeControlRequestHandler(BaseHTTPRequestHandler):
    judge: Optional['Judge'] = None

    def update_problems(self):
        if self.judge is not None:
            self.judge.update_problems()

    def do_POST(self):
        if self.path == '/update/problems':
            self.log_message('Problem update requested.')
            self.update_problems()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'As you wish.')
            return
        self.send_error(404)

    def do_GET(self):
        if self.path == '/metrics':
            self.log_message('Metrics requested.')
            self.send_response(200)
            self.end_headers()
            self.wfile.write(self.generate_prometheus().encode('utf-8'))
            return
        self.send_error(404)

    def generate_prometheus(self) -> str:
        lines = [
            '# HELP dmoj_judge_up signals whether this instance of the judge is up and running',
            '# TYPE dmoj_judge_up gauge',
            f'dmoj_judge_up {int(self.judge.packet_manager.online) if self.judge is not None else 0}',
            '',
            '# HELP dmoj_judge_problems the number of problems this judge has access to',
            '# TYPE dmoj_judge_problems gauge',
            f'dmoj_judge_problems {self.judge.problem_count if self.judge is not None else 0}',
            '',
            '# HELP dmoj_judge_grading whether this judge is currently grading a submission',
            '# TYPE dmoj_judge_grading gauge',
            f'dmoj_judge_grading {int(self.judge.grading) if self.judge is not None else 0}',
            '',
            '# HELP dmoj_judge_submission_graded the number of submissions this judge has graded',
            '# TYPE dmoj_judge_submission_graded counter',
            f'dmoj_judge_submission_graded_total {self.judge.submissions_graded if self.judge is not None else 0}',
            '',
            '# HELP dmoj_judge_case_verdicts_total the number of test cases granted this verdict',
            '# TYPE dmoj_judge_case_verdicts_total counter',
        ]

        if self.judge is not None:
            for verdict, count in self.judge.case_verdicts.items():
                lines.append(f'dmoj_judge_case_verdicts_total{{verdict="{verdict}"}} {count}')

        return '\n'.join(lines)
