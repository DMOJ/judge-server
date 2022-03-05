import errno
import json
import logging
import os
import socket
import ssl
import struct
import sys
import threading
import time
import traceback
import zlib
from typing import List, Optional, TYPE_CHECKING, Tuple

from dmoj import sysinfo
from dmoj.judgeenv import get_runtime_versions, get_supported_problems_and_mtimes
from dmoj.result import Result
from dmoj.utils.unicode import utf8bytes, utf8text

if TYPE_CHECKING:
    from dmoj.judge import Judge

log = logging.getLogger(__name__)


class JudgeAuthenticationFailed(Exception):
    pass


class PacketManager:
    SIZE_PACK = struct.Struct('!I')

    ssl_context: Optional[ssl.SSLContext]
    judge: 'Judge'

    def __init__(
        self,
        host: str,
        port: int,
        judge: 'Judge',
        name: str,
        key: str,
        secure: bool = False,
        no_cert_check: bool = False,
        cert_store: Optional[str] = None,
    ):
        self.host = host
        self.port = port
        self.judge = judge
        self.name = name
        self.key = key
        self._closed = False

        log.info('Preparing to connect to [%s]:%s as: %s', host, port, name)
        if secure:
            self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            self.ssl_context.options |= ssl.OP_NO_SSLv2
            self.ssl_context.options |= ssl.OP_NO_SSLv3

            if not no_cert_check:
                self.ssl_context.verify_mode = ssl.CERT_REQUIRED
                self.ssl_context.check_hostname = True

            if cert_store is None:
                self.ssl_context.load_default_certs()
            else:
                self.ssl_context.load_verify_locations(cafile=cert_store)
            log.info('Configured to use TLS.')
        else:
            self.ssl_context = None
            log.info('TLS not enabled.')

        self.secure = secure
        self.no_cert_check = no_cert_check
        self.cert_store = cert_store

        self._lock = threading.RLock()
        self._batch = 0
        self._testcase_queue_lock = threading.Lock()
        self._testcase_queue: List[Tuple[int, Result]] = []

        # Exponential backoff: starting at 4 seconds, max 60 seconds.
        # If it fails to connect for something like 7 hours, it could RecursionError.
        self.fallback = 4

        self.conn = None
        self._do_reconnect()

    def _connect(self):
        problems = get_supported_problems_and_mtimes()
        versions = get_runtime_versions()

        log.info('Opening connection to: [%s]:%s', self.host, self.port)

        while True:
            try:
                self.conn = socket.create_connection((self.host, self.port), timeout=5)
            except OSError as e:
                if e.errno != errno.EINTR:
                    raise
            else:
                break

        self.conn.settimeout(300)
        self.conn.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        if self.ssl_context:
            log.info('Starting TLS on: [%s]:%s', self.host, self.port)
            self.conn = self.ssl_context.wrap_socket(self.conn, server_hostname=self.host)

        log.info('Starting handshake with: [%s]:%s', self.host, self.port)
        self.input = self.conn.makefile('rb')
        self.handshake(problems, versions, self.name, self.key)
        log.info('Judge "%s" online: [%s]:%s', self.name, self.host, self.port)

    def _reconnect(self):
        log.warning('Attempting reconnection in %.0fs: [%s]:%s', self.fallback, self.host, self.port)

        if self.conn is not None:
            log.info('Dropping old connection.')
            self.conn.close()
        time.sleep(self.fallback)
        self.fallback = min(self.fallback * 1.5, 60)  # Limit fallback to one minute.
        self._do_reconnect()

    def _do_reconnect(self):
        try:
            self._connect()
        except JudgeAuthenticationFailed:
            log.error('Authentication as "%s" failed on: [%s]:%s', self.name, self.host, self.port)
            self._reconnect()
        except socket.error:
            log.exception('Connection failed due to socket error: [%s]:%s', self.host, self.port)
            self._reconnect()

    def __del__(self):
        self.close()

    def close(self):
        if self.conn and not self._closed:
            try:
                # May already be closed despite self._closed == False if a network error occurred and `close` is being
                # called as part of cleanup.
                self.conn.shutdown(socket.SHUT_RDWR)
            except socket.error:
                pass
        self._closed = True

    def _read_forever(self):
        try:
            while True:
                self._receive_packet(self._read_single())
        except KeyboardInterrupt:
            pass
        except Exception:  # connection reset by peer
            log.exception('Exception while reading packet from site, will not attempt to reconnect! Quitting judge.')
            # TODO(tbrindus): this is really sad. This isn't equivalent to `raise SystemExit(1)` since we're not on the
            # main thread, and doing the latter would only exit the network thread. We should fix mid-grading reconnects
            # so that we don't need this sledgehammer approach that relies on Docker restarting the judge for us.
            os._exit(1)

    def _read_single(self) -> dict:
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
            packet = zlib.decompress(self.input.read(size))
        except zlib.error:
            self._reconnect()
            return self._read_single()
        else:
            return json.loads(utf8text(packet))

    def run(self):
        threading.Thread(target=self._periodically_flush_testcase_queue).start()
        self._read_forever()

    def disconnect(self):
        self.close()
        self.judge.abort_grading()
        sys.exit(0)

    def _flush_testcase_queue(self):
        with self._testcase_queue_lock:
            if not self._testcase_queue:
                return

            self._send_packet(
                {
                    'name': 'test-case-status',
                    'submission-id': self.judge.current_submission.id,
                    'cases': [
                        {
                            'position': position,
                            'status': result.result_flag,
                            'time': result.execution_time,
                            'points': result.points,
                            'total-points': result.total_points,
                            'memory': result.max_memory,
                            'output': result.output,
                            'extended-feedback': result.extended_feedback,
                            'feedback': result.feedback,
                            'voluntary-context-switches': result.context_switches[0],
                            'involuntary-context-switches': result.context_switches[1],
                            'runtime-version': result.runtime_version,
                        }
                        for position, result in self._testcase_queue
                    ],
                }
            )

            self._testcase_queue.clear()

    def _periodically_flush_testcase_queue(self):
        while not self._closed:
            try:
                time.sleep(0.25)
                # It is okay if we flush the testcase queue even while the connection is not open or there's nothing
                # grading, since the only thing that can queue testcases is a currently-grading submission.
                self._flush_testcase_queue()
            except KeyboardInterrupt:
                break
            except Exception:
                traceback.print_exc()

    def _send_packet(self, packet: dict):
        for k, v in packet.items():
            if isinstance(v, bytes):
                # Make sure we don't have any garbage utf-8 from e.g. weird compilers
                # *cough* fpc *cough* that could cause this routine to crash
                # We cannot use utf8text because it may not be text.
                packet[k] = v.decode('utf-8', 'replace')

        raw = zlib.compress(utf8bytes(json.dumps(packet)))
        with self._lock:
            try:
                assert self.conn is not None
                self.conn.sendall(PacketManager.SIZE_PACK.pack(len(raw)) + raw)
            except Exception:  # connection reset by peer
                log.exception('Exception while sending packet to site, will not attempt to reconnect! Quitting judge.')
                os._exit(1)

    def _receive_packet(self, packet: dict):
        name = packet['name']
        if name == 'ping':
            self.ping_packet(packet['when'])
        elif name == 'get-current-submission':
            self.current_submission_packet()
        elif name == 'submission-request':
            self.submission_acknowledged_packet(packet['submission-id'])
            from dmoj.judge import Submission

            self.judge.begin_grading(
                Submission(
                    id=packet['submission-id'],
                    problem_id=packet['problem-id'],
                    language=packet['language'],
                    source=packet['source'],
                    time_limit=float(packet['time-limit']),
                    memory_limit=int(packet['memory-limit']),
                    short_circuit=packet['short-circuit'],
                    meta=packet['meta'],
                )
            )
            self._batch = 0
            log.info(
                'Accept submission: %d: executor: %s, code: %s',
                packet['submission-id'],
                packet['language'],
                packet['problem-id'],
            )
        elif name == 'terminate-submission':
            self.judge.abort_grading()
        elif name == 'disconnect':
            log.info('Received disconnect request, shutting down...')
            self.disconnect()
        else:
            log.error('Unknown packet %s, payload %s', name, packet)

    def handshake(self, problems: str, runtimes, id: str, key: str):
        self._send_packet({'name': 'handshake', 'problems': problems, 'executors': runtimes, 'id': id, 'key': key})
        log.info('Awaiting handshake response: [%s]:%s', self.host, self.port)
        try:
            data = self.input.read(PacketManager.SIZE_PACK.size)
            size = PacketManager.SIZE_PACK.unpack(data)[0]
            packet = utf8text(zlib.decompress(self.input.read(size)))
            resp = json.loads(packet)
        except Exception:
            log.exception('Cannot understand handshake response: [%s]:%s', self.host, self.port)
            raise JudgeAuthenticationFailed()
        else:
            if resp['name'] != 'handshake-success':
                log.error('Handshake failed.')
                raise JudgeAuthenticationFailed()

    def supported_problems_packet(self, problems: List[Tuple[str, int]]):
        log.debug('Update problems')
        self._send_packet({'name': 'supported-problems', 'problems': problems})

    def test_case_status_packet(self, position: int, result: Result):
        log.debug(
            'Test case on %d: #%d, %s [%.3fs | %.2f MB], %.1f/%.0f',
            self.judge.current_submission.id,
            position,
            ', '.join(result.readable_codes()),
            result.execution_time,
            result.max_memory / 1024.0,
            result.points,
            result.total_points,
        )
        with self._testcase_queue_lock:
            self._testcase_queue.append((position, result))

    def compile_error_packet(self, message: str):
        log.debug('Compile error: %d', self.judge.current_submission.id)
        self.fallback = 4
        self._send_packet({'name': 'compile-error', 'submission-id': self.judge.current_submission.id, 'log': message})

    def compile_message_packet(self, message: str):
        log.debug('Compile message: %d', self.judge.current_submission.id)
        self._send_packet(
            {'name': 'compile-message', 'submission-id': self.judge.current_submission.id, 'log': message}
        )

    def internal_error_packet(self, message: str):
        log.debug('Internal error: %d', self.judge.current_submission.id)
        self._flush_testcase_queue()
        self._send_packet(
            {'name': 'internal-error', 'submission-id': self.judge.current_submission.id, 'message': message}
        )

    def begin_grading_packet(self, is_pretested: bool):
        log.debug('Begin grading: %d', self.judge.current_submission.id)
        self._send_packet(
            {'name': 'grading-begin', 'submission-id': self.judge.current_submission.id, 'pretested': is_pretested}
        )

    def grading_end_packet(self):
        log.debug('End grading: %d', self.judge.current_submission.id)
        self.fallback = 4
        self._flush_testcase_queue()
        self._send_packet({'name': 'grading-end', 'submission-id': self.judge.current_submission.id})

    def batch_begin_packet(self):
        self._batch += 1
        log.debug('Enter batch number %d: %d', self._batch, self.judge.current_submission.id)
        self._flush_testcase_queue()
        self._send_packet({'name': 'batch-begin', 'submission-id': self.judge.current_submission.id})

    def batch_end_packet(self):
        log.debug('Exit batch number %d: %d', self._batch, self.judge.current_submission.id)
        self._flush_testcase_queue()
        self._send_packet({'name': 'batch-end', 'submission-id': self.judge.current_submission.id})

    def current_submission_packet(self):
        log.debug('Current submission query: %d', self.judge.current_submission.id)
        self._send_packet({'name': 'current-submission-id', 'submission-id': self.judge.current_submission.id})

    def submission_aborted_packet(self):
        log.debug('Submission aborted: %d', self.judge.current_submission.id)
        self._flush_testcase_queue()
        self._send_packet({'name': 'submission-terminated', 'submission-id': self.judge.current_submission.id})

    def ping_packet(self, when: float):
        data = {'name': 'ping-response', 'when': when, 'time': time.time()}
        for fn in sysinfo.report_callbacks:
            key, value = fn()
            data[key] = value
        self._send_packet(data)

    def submission_acknowledged_packet(self, sub_id: int):
        self._send_packet({'name': 'submission-acknowledged', 'submission-id': sub_id})
