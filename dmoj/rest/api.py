import json
from hashlib import md5

from pydantic import BaseModel

from dmoj.rest import cache
from dmoj.rest.app import app
from dmoj.judge import Submission


@app.post('/api/gen-judge-config')
async def gen_judge_config():
    pass


@app.get('/api/submission/{submission_id}')
async def get_submission(submission_id: str):
    submission = await cache.get(submission_id)
    return json.loads(submission or '{}')


class SubmissionInput(BaseModel):
    id: str
    language_id: int
    judge_config: str
    judge_config_url: str
    source_code: str
    time_limit: int
    memory_limit: int


@app.post('/api/submission')
async def create_submission(submission: SubmissionInput):
    app.state.judge.submission_id_counter += 1
    problem_id = md5(submission.judge_config.encode()).hexdigest(),
    app.state.judge.graded_submissions.append((submission))
    # judge.graded_submissions.append((problem_id, language_id, src, time_limit, memory_limit))
    app.state.judge.begin_grading(Submission(
        submission.id,
        problem_id,
        submission.judge_config,
        submission.language_id,
        submission.source_code,
        submission.time_limit,
        submission.memory_limit,
        False,
        {}
    ))
