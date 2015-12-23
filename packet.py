import json
import logging
import socket
import struct
import sys
import threading
import time
import traceback
import zlib
from operator import itemgetter

import pika
import pika.exceptions

import sysinfo

from executors import executors

logger = logging.getLogger('dmoj.judge')


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
        self._connect()
        # Exponential backoff: starting at 4 seconds.
        # Certainly hope it won't stack overflow, since it will take days if not years.
        self.fallback = 4

    def _connect(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((self.host, self.port))
        self.input = self.conn.makefile('r')
        self.output = self.conn.makefile('w', 0)
        self.handshake(self.judge.supported_problems(), self.name, self.key)

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
        self.conn.shutdown()

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
        if packet['name'] not in ['ping-response', 'handshake', 'test-case-status']:
            print '%s:%s => %s' % (self.host, self.port, json.dumps(packet, indent=4))

        raw = json.dumps(packet).encode('zlib')
        with self._lock:
            self.output.write(PacketManager.SIZE_PACK.pack(len(raw)))
            self.output.write(raw)

    def _receive_packet(self, packet):
        if packet['name'] != 'ping':
            print '%s:%s <= %s' % (self.host, self.port, json.dumps(packet, indent=4))

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
        self.fallback = 4
        self._send_packet({'name': 'compile-error',
                           'submission-id': self.judge.current_submission,
                           'log': log})

    def compile_message_packet(self, log):
        self._send_packet({'name': 'compile-message',
                           'submission-id': self.judge.current_submission,
                           'log': log})

    def internal_error_packet(self, message):
        self._send_packet({'name': 'internal-error',
                           'submission-id': self.judge.current_submission,
                           'message': message})

    def begin_grading_packet(self):
        self._send_packet({'name': 'grading-begin',
                           'submission-id': self.judge.current_submission})

    def grading_end_packet(self):
        self.fallback = 4
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


class AMQPPacketManager(object):
    def __init__(self, judge, url, name, key):
        self.judge = judge
        self.name = name

        self.params = pika.URLParameters(url)
        self.params.credentials = pika.PlainCredentials(name, key)

        self.running = False

    def _connect(self):
        self.conn = pika.BlockingConnection(self.params)
        self.submission_tag = None
        self._in_batch = False
        self._batch = 0
        self._id = None
        self._start = time.time()
        self.problems = set()
        self._latency = 1

    def _broadcast_listener(self, chan, method, properties, body):
        try:
            packet = json.loads(body.decode('zlib'))
            if packet['action'] == 'abort-submission':
                if packet['id'] == self._id:
                    logger.info('Received abortion request: %d', packet['id'])
                    self.judge.terminate_grading()
                else:
                    logger.info('Ignored abortion request: %d', packet['id'])
        except Exception:
            logger.exception('Error in AMQP broadcast listener')
            return

    def _latency_listener(self, chan, method, properties, body):
        try:
            packet = json.loads(body.decode('zlib'))
            if 'client' in packet:
                self._latency = time.time() - packet['client']
                logger.debug('Ping time measured: %.3fs', self._latency)
        except Exception:
            logger.exception('Error in AMQP latency listener')
            return

    def _send_latency(self):
        self.receiver.basic_publish(exchange='', routing_key='latency', body=json.dumps({
            'queue': self.latency_queue, 'time': time.time(),
        }).encode('zlib'))

    def _submission_listener(self, chan, method, properties, body):
        assert self._id is None

        try:
            packet = json.loads(body.decode('zlib'))
            args = (
                packet['id'],
                packet['problem'],
                packet['language'],
                packet['source'],
                float(packet['time-limit']),
                int(packet['memory-limit']),
                packet['short-circuit']
            )
        except Exception:
            logger.exception('Error in AMQP submission reception')
            chan.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        if packet['language'] not in executors or packet['problem'] not in self.problems:
            logger.info('Reject submission: %d: executor: %s, code: %s',
                        packet['id'], packet['language'], packet['problem'])
            chan.basic_nack(delivery_tag=method.delivery_tag)
            return

        self.submission_tag = method.delivery_tag
        self._in_batch = False
        self._batch = 0
        self._id = packet['id']
        self._send_judge_packet({'name': 'acknowledged'})

        logger.info('Accept submission: %d: executor: %s, code: %s',
                    packet['id'], packet['language'], packet['problem'])
        self.judge.begin_grading(*args)

    def _run(self):
        self._connect()
        self.running = True

        self.submission_chan = self.conn.channel()
        self.submission_chan.basic_qos(prefetch_count=1)
        self.submission_chan.basic_consume(self._submission_listener, queue='submission')

        self.receiver = self.conn.channel()
        broadcast_queue = self.receiver.queue_declare(exclusive=True).method.queue
        self.latency_queue = self.receiver.queue_declare(exclusive=True).method.queue
        self.receiver.queue_bind(queue=broadcast_queue, exchange='broadcast')
        self.receiver.basic_consume(self._broadcast_listener, queue=broadcast_queue, no_ack=True)
        self.receiver.basic_consume(self._latency_listener, queue=self.latency_queue, no_ack=True)

        self.supported_executors_packet()
        self.supported_problems_packet(self.judge.supported_problems())

        last_ping = 0
        while self.running:
            now = time.time()
            if last_ping + 10 < now:
                self.ping_packet()
                self._send_latency()
                last_ping = now

            self.conn.process_data_events(time_limit=last_ping + 10 - now)

    def submission_done(self, ack=True):
        logger.info('Finished submission: %d', self._id)
        self._id = None
        if ack:
            self.submission_chan.basic_ack(delivery_tag=self.submission_tag)
        else:
            self.submission_chan.basic_nack(delivery_tag=self.submission_tag)

    def _send_judge_packet(self, packet):
        packet['id'] = self._id
        packet['judge'] = self.name
        logger.debug('Judge channel: %s', packet)
        self.submission_chan.basic_publish(exchange='', routing_key='sub-%d' % self._id, body=json.dumps(packet).encode('zlib'))

    def _send_ping_packet(self, packet):
        packet['judge'] = self.name
        logger.debug('Ping channel: %s', packet)
        self.submission_chan.basic_publish(exchange='', routing_key='judge-ping', body=json.dumps(packet).encode('zlib'))

    def supported_problems_packet(self, problems):
        self.problems = set(map(itemgetter(0), problems))
        logger.info('Update problems')
        self._send_ping_packet({
            'name': 'problem-update',
            'problems': list(self.problems),
        })

    def supported_executors_packet(self):
        logger.info('Update executors: %s', executors.keys())
        self._send_ping_packet({
            'name': 'executor-update',
            'executors': executors.keys(),
        })

    def ping_packet(self):
        packet = {'name': 'ping', 'start': self._start, 'latency': self._latency}
        for fn in sysinfo.report_callbacks:
            key, value = fn()
            packet[key] = value
        self._send_ping_packet(packet)

    def begin_grading_packet(self):
        logger.info('Begin grading: %d', self._id)
        self._send_judge_packet({'name': 'grading-begin'})

    def grading_end_packet(self):
        logger.info('End grading: %d', self._id)
        self._send_judge_packet({'name': 'grading-end'})
        self.submission_done()

    def begin_batch_packet(self):
        self._batch += 1
        self._in_batch = True
        logger.info('Enter batch number %d: %d', self._batch, self._id)

    def batch_end_packet(self):
        self._in_batch = False
        logger.info('Exit batch number %d: %d', self._batch, self._id)

    def compile_error_packet(self, log):
        self._send_judge_packet({
            'name': 'compile-error',
            'log': log,
        })
        logger.info('Compile error: %d', self._id)
        self.submission_done()

    def compile_message_packet(self, log):
        logger.info('Compile message: %d', self._id)
        self._send_judge_packet({
            'name': 'compile-message',
            'log': log,
        })

    def internal_error_packet(self, message):
        logger.info('Internal error: %d', self._id)
        self._send_judge_packet({
            'name': 'internal-error',
            'message': message,
        })
        self.submission_done(ack=False)

    def submission_terminated_packet(self):
        logger.info('Submission aborted: %d', self._id)
        self._send_judge_packet({'name': 'aborted'})
        self.submission_done()

    def test_case_status_packet(self, position, points, total_points, status, time, memory, output, feedback=None):
        logger.info('Submission test case #%d: %d', position, self._id)
        self._send_judge_packet({
            'name': 'test-case',
            'position': position,
            'status': status,
            'time': time,
            'points': points,
            'total-points': total_points,
            'memory': memory,
            'batch': self._batch if self._in_batch else None,
            'output': output,
            'feedback': feedback,
        })

    def stop(self):
        self.submission_chan.stop_consuming()
        self.receiver.stop_consuming()

    def run(self):
        while True:
            try:
                self._run()
            except pika.exceptions.ConnectionClosed:
                logger.error('Disconnected')
                continue
            except KeyboardInterrupt:
                logger.info('Terminating...')
                self.stop()
            except Exception:
                logger.exception('Exception in pika loop')
            break

    def run_async(self):
        threading.Thread(target=self.run).start()
