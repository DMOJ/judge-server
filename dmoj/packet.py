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
from operator import itemgetter

import pika
import pika.exceptions

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
        self._connect()
        # Exponential backoff: starting at 4 seconds.
        # Certainly hope it won't stack overflow, since it will take days if not years.
        self.fallback = 4

    def _connect(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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

    def batch_begin_packet(self):
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
        self._reset()

    def _connect(self):
        logger.info('Creating connection...')
        self.conn = pika.SelectConnection(self.params, on_open_callback=self.on_connection_open,
                                          stop_ioloop_on_close=False)

    def _reconnect(self):
        self.conn.ioloop.stop()

        if self.running:
            self._connect()
            self.conn.ioloop.start()

    def on_connection_open(self, connection):
        logger.info('Connection opened')

        self._reset()
        self.conn.add_on_close_callback(self.on_connection_closed)

        self.conn.channel(self.on_submission_channel_create)
        self.conn.channel(self.on_receiver_channel_create)

    def on_connection_closed(self, connection, reply_code, reply_text):
        if self.running:
            logger.error('Disconnected, reconnecting in 5 seconds')
            self.conn.add_timeout(5, self._reconnect)
        else:
            logger.info('Gracefully exiting event loop')
            self.conn.ioloop.stop()

    def _reset(self):
        self.submission_tag = None
        self._in_batch = False
        self._batch = 0
        self._id = None
        self._start = time.time()
        self.problems = set()
        self._latency = 1
        self.submission_consumers = []

    def on_receiver_channel_create(self, channel):
        logger.info('Created message channel')

        self.receiver_chan = channel

        def on_latency_queue_declare(frame):
            self.latency_queue = frame.method.queue
            channel.basic_consume(self.on_latency_message, queue=self.latency_queue, no_ack=True)

            logger.info('Starting to ping...')
            self.ping_packet()
            self._send_latency()

            self.supported_executors_packet()
            self.supported_problems_packet(get_supported_problems())

        def on_broadcast_queue_bind(frame):
            channel.basic_consume(self.on_broadcast_message, queue=self.broadcast_queue, no_ack=True)

        def on_broadcast_queue_declare(frame):
            self.broadcast_queue = frame.method.queue
            channel.queue_bind(on_broadcast_queue_bind, queue=self.broadcast_queue, exchange='broadcast')

        channel.queue_declare(on_broadcast_queue_declare, exclusive=True)
        channel.queue_declare(on_latency_queue_declare, exclusive=True)

    def on_broadcast_message(self, chan, method, properties, body):
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

    def on_latency_message(self, chan, method, properties, body):
        try:
            packet = json.loads(body.decode('zlib'))
            if 'client' in packet:
                self._latency = timer() - packet['client']
                logger.debug('Ping time measured: %.3fs', self._latency)
        except Exception:
            logger.exception('Error in AMQP latency listener')
            return

    def _send_latency(self):
        self.conn.add_timeout(10, self._send_latency)
        self.receiver_chan.basic_publish(exchange='', routing_key='latency', body=json.dumps({
            'queue': self.latency_queue, 'time': timer(),
        }).encode('zlib'))

    def on_submission_channel_create(self, channel):
        logger.info('Created submission channel')

        self.submission_chan = channel

        channel.basic_qos(prefetch_count=1)
        self.submission_consumers.append(channel.basic_consume(self.on_submission_request, queue='submission'))

    def on_submission_request(self, chan, method, properties, body):
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

    def submission_done(self, ack=True):
        logger.info('Finished submission: %d', self._id)
        self._id = None
        if ack:
            self.submission_chan.basic_ack(delivery_tag=self.submission_tag)
        else:
            self.submission_chan.basic_nack(delivery_tag=self.submission_tag, requeue=False)

    def _send_judge_packet(self, packet):
        packet['id'] = self._id
        packet['judge'] = self.name
        logger.debug('Judge channel: %s', packet)
        self.submission_chan.basic_publish(exchange='', routing_key='sub-%d' % self._id,
                                           body=json.dumps(packet).encode('zlib'))

    def _send_ping_packet(self, packet):
        packet['judge'] = self.name
        logger.debug('Ping channel: %s', packet)
        self.submission_chan.basic_publish(exchange='', routing_key='judge-ping',
                                           body=json.dumps(packet).encode('zlib'))

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
        self.conn.add_timeout(10, self.ping_packet)

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

    def batch_begin_packet(self):
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
        self.running = False
        self.submission_chan.close()
        self.receiver_chan.close()
        self.conn.ioloop.stop()

    def run(self):
        logger.info('Starting packet manager...')
        self.running = True
        self._connect()
        try:
            logger.info('Starting IO loop...')
            self.conn.ioloop.start()
        except KeyboardInterrupt:
            self.stop()
        except Exception:
            logger.exception('Exception in pika loop')
            raise SystemExit(1)

    def run_async(self):
        threading.Thread(target=self.run).start()
