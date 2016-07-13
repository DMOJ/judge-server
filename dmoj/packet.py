import json
import logging
import socket
import struct
import sys
import threading
import time
import traceback
import zlib
import os

from dmoj import sysinfo
from dmoj.executors import executors
from dmoj.judgeenv import get_supported_problems

logger = logging.getLogger('dmoj.judge')
timer = time.clock if os.name == 'nt' else time.time


class JudgeAuthenticationFailed(Exception):
    pass


class PacketManager(object):
    SIZE_PACK = struct.Struct('!I')

    def __init__(self, host, port, judge, name, key):
        self.host = host
        self.port = port
        self.judge = judge
        self.name = name
        self.key = key
        self._lock = threading.RLock()
        self._batch = 0
        # Exponential backoff: starting at 4 seconds.
        # Certainly hope it won't stack overflow, since it will take days if not years.
        self.fallback = 4

        try:
            self._connect()
        except JudgeAuthenticationFailed:
            self._reconnect()

    def _connect(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.conn.connect((self.host, self.port))
        self.input = self.conn.makefile('r')
        self.output = self.conn.makefile('w', 0)
        self.handshake(get_supported_problems(), self.name, self.key)

    def _reconnect(self):
        if self.fallback > 65536:
            # Return 0 to avoid supervisor restart.
            raise SystemExit(0)
        print>> sys.stderr
        print>> sys.stderr, 'SOCKET ERROR: Disconnected! Reconnecting in %d seconds.' % self.fallback
        self.conn.close()
        time.sleep(self.fallback)
        self.fallback *= 1.5
        try:
            self._connect()
        except JudgeAuthenticationFailed:
            self._reconnect()

    def __del__(self):
        self.conn.shutdown(socket.SHUT_RDWR)

    def _read_async(self):
        try:
            while True:
                self._receive_packet(self._read_single())
        except KeyboardInterrupt:
            pass
        except Exception:  # connection reset by peer
            traceback.print_exc()
            raise SystemExit(1)

    def _read_single(self):
        try:
            data = self.input.read(PacketManager.SIZE_PACK.size)
        except socket.error:
            self._reconnect()
            return self._read_single()
        if not data:
            self._reconnect()
            return self._read_single()
        size = PacketManager.SIZE_PACK.unpack(data)[0]
        try:
            packet = self.input.read(size).decode('zlib')
        except zlib.error:
            self._reconnect()
            return self._read_single()
        else:
            return json.loads(packet)

    def run(self):
        self._read_async()

    def run_async(self):
        threading.Thread(target=self._read_async).start()

    def _send_packet(self, packet):
        raw = json.dumps(packet).encode('zlib')
        with self._lock:
            self.output.write(PacketManager.SIZE_PACK.pack(len(raw)))
            self.output.write(raw)

    def _receive_packet(self, packet):
        name = packet['name']
        if name == 'ping':
            self.ping_packet(packet['when'])
        elif name == 'get-current-submission':
            self.current_submission_packet()
        elif name == 'submission-request':
            self.submission_acknowledged_packet(packet['submission-id'])
            self.judge.begin_grading(
                packet['submission-id'],
                packet['problem-id'],
                packet['language'],
                packet['source'],
                float(packet['time-limit']),
                int(packet['memory-limit']),
                packet['short-circuit']
            )
            self._batch = 0
            logger.info('Accept submission: %d: executor: %s, code: %s',
                        packet['submission-id'], packet['language'], packet['problem-id'])
        elif name == 'terminate-submission':
            self.judge.terminate_grading()
        else:
            print 'ERROR: unknown packet %s, payload %s' % (name, packet)

    def handshake(self, problems, id, key):
        self._send_packet({'name': 'handshake',
                           'problems': problems,
                           'executors': executors.keys(),
                           'id': id,
                           'key': key})
        try:
            data = self.input.read(PacketManager.SIZE_PACK.size)
            size = PacketManager.SIZE_PACK.unpack(data)[0]
            packet = self.input.read(size).decode('zlib')
            resp = json.loads(packet)
        except Exception:
            traceback.print_exc()
            raise JudgeAuthenticationFailed()
        else:
            if resp['name'] != 'handshake-success':
                raise JudgeAuthenticationFailed()

    def supported_problems_packet(self, problems):
        logger.info('Update problems')
        self._send_packet({'name': 'supported-problems',
                           'problems': problems})

    def test_case_status_packet(self, position, points, total_points, status, time, memory, output, feedback=None):
        self._send_packet({'name': 'test-case-status',
                           'submission-id': self.judge.current_submission,
                           'position': position,
                           'status': status,
                           'time': time,
                           'points': points,
                           'total-points': total_points,
                           'memory': memory,
                           'output': output,
                           'feedback': feedback})

    def compile_error_packet(self, log):
        logger.info('Compile error: %d', self.judge.current_submission)
        self.fallback = 4
        self._send_packet({'name': 'compile-error',
                           'submission-id': self.judge.current_submission,
                           'log': log})

    def compile_message_packet(self, log):
        logger.info('Compile message: %d', self.judge.current_submission)
        self._send_packet({'name': 'compile-message',
                           'submission-id': self.judge.current_submission,
                           'log': log})

    def internal_error_packet(self, message):
        logger.info('Internal error: %d', self.judge.current_submission)
        self._send_packet({'name': 'internal-error',
                           'submission-id': self.judge.current_submission,
                           'message': message})

    def begin_grading_packet(self):
        logger.info('Begin grading: %d', self.judge.current_submission)
        self._send_packet({'name': 'grading-begin',
                           'submission-id': self.judge.current_submission})

    def grading_end_packet(self):
        logger.info('End grading: %d', self.judge.current_submission)
        self.fallback = 4
        self._send_packet({'name': 'grading-end',
                           'submission-id': self.judge.current_submission})

    def batch_begin_packet(self):
        self._batch += 1
        logger.info('Enter batch number %d: %d', self._batch, self.judge.current_submission)
        self._send_packet({'name': 'batch-begin',
                           'submission-id': self.judge.current_submission})

    def batch_end_packet(self):
        logger.info('Exit batch number %d: %d', self._batch, self.judge.current_submission)
        self._send_packet({'name': 'batch-end',
                           'submission-id': self.judge.current_submission})

    def current_submission_packet(self):
        logger.info('Current submission query: %d', self.judge.current_submission)
        self._send_packet({'name': 'current-submission-id',
                           'submission-id': self.judge.current_submission})

    def submission_terminated_packet(self):
        logger.info('Submission aborted: %d', self.judge.current_submission)
        self._send_packet({'name': 'submission-terminated',
                           'submission-id': self.judge.current_submission})

    def ping_packet(self, when):
        data = {'name': 'ping-response',
                'when': when,
                'time': time.time()}
        for fn in sysinfo.report_callbacks:
            key, value = fn()
            data[key] = value
        self._send_packet(data)

    def submission_acknowledged_packet(self, sub_id):
        self._send_packet({'name': 'submission-acknowledged',
                           'submission-id': sub_id})


