import os, sys, connexion, six, logging
from dmoj import judgeenv, executors
from dmoj.judge import Judge
from flask import jsonify, current_app
from operator import itemgetter
from flask import g
from enum import Enum
from base64 import b64decode

class JudgeState(Enum):
    FAILED = 0
    SUCCESS = 1

class LocalPacketManager(object):
    def __init__(self, judge):
        self.judge = judge

    def _receive_packet(self, packet):
        pass

    def supported_problems_packet(self, problems):
        pass

    def test_case_status_packet(self, position, result):
        self.judge.graded_submissions[-1]['testCaseStatus'] = result.readable_codes()

    def compile_error_packet(self, message):
        self.judge.graded_submissions[-1]['compileError'].append(message)

    def compile_message_packet(self, message):
        self.judge.graded_submissions[-1]['compileMessage'].append(message)

    def internal_error_packet(self, message):
        self.judge.graded_submissions[-1]['internalError'].append(message)

    def begin_grading_packet(self, is_pretested):
        pass

    def grading_end_packet(self):
        pass

    def batch_begin_packet(self):
        pass

    def batch_end_packet(self):
        pass

    def current_submission_packet(self):
        pass

    def submission_terminated_packet(self):
        pass

    def submission_acknowledged_packet(self, sub_id):
        pass

    def run(self):
        pass

    def close(self):
        pass


class LocalJudge(Judge):
    def __init__(self):
        super(LocalJudge, self).__init__()
        self.packet_manager = LocalPacketManager(self)
        self.next_submission_id = 0
        self.graded_submissions = []

def get_judge():
    judge = getattr(g, '_judge', None)
    if judge is None:
        g._judge = LocalJudge()
    return g._judge

# POST /submission
def add_submission(body):
    judge = get_judge()
    body = connexion.request.get_json()
    problem_id = body['problemId']
    language_id = body['languageId']
    time_limit = body['timeLimit']
    memory_limit = body['memoryLimit']
    source = body['sourceCode']

    if problem_id not in map(itemgetter(0), judgeenv.get_supported_problems()):
        return jsonify({
            'error': "unknown problem %s" % problem_id
        }), 405
    
    if language_id not in executors.executors:
        return jsonify({'error': "unknown languae %s" % language_id}), 405

    if time_limit <= 0:
        return jsonify({'error': "timeLimit must be >= 0"}), 405

    if memory_limit <= 0:
        return jsonify({'error': "memoryLimit must be >= 0"}), 405

    submission_id = judge.next_submission_id
    
    judge.graded_submissions.append({
        "submissionId":  submission_id,
        "problemId": problem_id,
        "languageId": language_id,
        "sourceCode": source,
        "timeLimit": time_limit,
        "memoryLimit": memory_limit,
        "compileError": [],
        "compileMessage": [],
        "testCaseResults": [],
        "internalError":[]
    })

    source = b64decode(source).decode('utf-8')
    print(source)
    judge.begin_grading(submission_id, problem_id, language_id, source, time_limit,
                        memory_limit, False, False, blocking=True)

    judge.next_submission_id += 1
    
    return jsonify(judge.graded_submissions[submission_id]), 200

# GET /submissionResult/{submissionId}
def submission_result_get(submissionId):
    judge = get_judge()
    return jsonify(judge.graded_submissions[submission_id]), 200

def main():
    judgeenv.load_env(cli=True)
    executors.load_executors()

    logging.basicConfig(filename=judgeenv.log_file, level=logging.INFO,
                        format='%(levelname)s %(asctime)s %(module)s %(message)s')

    for warning in judgeenv.startup_warnings:
        print(ansi_style('#ansi[Warning: %s](yellow)' % warning))
    del judgeenv.startup_warnings
    print()
    
    server = connexion.FlaskApp(__name__, specification_dir='api/')
    with server.app.app_context():
        judge = get_judge()
        judge.listen()
        server.add_api('api.yaml')
        server.run(port=8080)

if __name__ == '__main__':
    main()
