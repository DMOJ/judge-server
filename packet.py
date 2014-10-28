import json
import zlib
import socket
import threading
import struct
import traceback
import time
from executors import executors
import sysinfo


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
        self._connect()

    def _connect(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((self.host, self.port))
        self.input = self.conn.makefile('r')
        self.output = self.conn.makefile('w', 0)
        self.handshake(self.judge.supported_problems(), self.key, self.name)

    def _reconnect(self):
        self.conn.close()
        self._connect()

    def __del__(self):
        self.conn.shutdown()

    def _read_async(self):
        try:
            while True:
                self._recieve_packet(self._read_single())
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
            return
        if not data:
            self._reconnect()
            return
        size = PacketManager.SIZE_PACK.unpack(data)[0]
        try:
            packet = self.input.read(size).decode('zlib')
        except zlib.error:
            self._reconnect()
        else:
            return json.loads(packet)

    def run(self):
        self._read_async()

    def run_async(self):
        threading.Thread(target=self._read_async).start()

    def _send_packet(self, packet):
        if packet['name'] not in ['ping-response', 'handshake', 'test-case-status']:
            print '%s:%s => %s' % (self.host, self.port, json.dumps(packet, indent=4))

        raw = json.dumps(packet).encode('zlib')
        self.output.write(PacketManager.SIZE_PACK.pack(len(raw)))
        self.output.write(raw)

    def _recieve_packet(self, packet):
        if packet['name'] != 'ping':
            print '%s:%s <= %s' % (self.host, self.port, json.dumps(packet, indent=4))

        name = packet['name']
        if name == 'ping':
            self.ping_packet(time.time())
        elif name == 'get-current-submission':
            self.current_submission_packet()
        elif name == 'submission-request':
            self.submission_acknowledged_packet(packet['submission-id'])
            self.judge.begin_grading(
                packet['submission-id'],
                packet['problem-id'],
                packet['language'],
                packet['source'],
                int(packet['time-limit']),
                int(packet['memory-limit']),
                packet['short-circuit']
            )
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
            resp = self._read_single()
        except Exception:
            traceback.print_exc()
            raise JudgeAuthenticationFailed()
        else:
            if resp['name'] != 'handshake-success':
                raise JudgeAuthenticationFailed()

    def supported_problems_packet(self, problems):
        self._send_packet({'name': 'supported-problems',
                           'problems': problems})

    def test_case_status_packet(self, position, points, total_points, status, time, memory, output):
        self._send_packet({'name': 'test-case-status',
                           'submission-id': self.judge.current_submission,
                           'position': position,
                           'status': status,
                           'time': time,
                           'points': points,
                           'total-points': total_points,
                           'memory': memory,
                           'output': output})

    def compile_error_packet(self, log):
        self._send_packet({'name': 'compile-error',
                           'submission-id': self.judge.current_submission,
                           'log': log})

    def compile_message_packet(self, log):
        self._send_packet({'name': 'compile-message',
                           'submission-id': self.judge.current_submission,
                           'log': log})

    def problem_not_exist_packet(self, problem):
        self._send_packet({'name': 'problem-not-exist',
                           'submission-id': self.judge.current_submission,
                           'problem': problem})

    def begin_grading_packet(self):
        self._send_packet({'name': 'grading-begin',
                           'submission-id': self.judge.current_submission})

    def grading_end_packet(self):
        self._send_packet({'name': 'grading-end',
                           'submission-id': self.judge.current_submission})

    def begin_batch_packet(self):
        self._send_packet({'name': 'batch-begin',
                           'submission-id': self.judge.current_submission})

    def batch_end_packet(self):
        self._send_packet({'name': 'batch-end',
                           'submission-id': self.judge.current_submission})

    def current_submission_packet(self):
        self._send_packet({'name': 'current-submission-id',
                           'submission-id': self.judge.current_submission})

    def submission_terminated_packet(self):
        traceback.print_exc()
        try:
            raise ValueError()
        except ValueError:
            traceback.print_exc()
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
