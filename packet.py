import json
import socket
import threading
import struct
import traceback


class PacketManager(object):
    SIZE_PACK = struct.Struct("!I")

    def __init__(self, host, port, judge):
        self.host = host
        self.port = port
        self.judge = judge
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((host, port))
        self.input = self.conn.makefile("r")
        self.output = self.conn.makefile("w", 0)

    def _read_async(self):
        try:
            while True:
                size = PacketManager.SIZE_PACK.unpack(self.input.read(PacketManager.SIZE_PACK.size))[0]
                packet = self.input.read(size).decode("zlib")
                packet = json.loads(packet)
                self._recieve_packet(packet)
        except KeyboardInterrupt:
            pass
        except Exception: # connection reset by peer
            traceback.print_exc()

    def run(self):
        self._read_async()
    
    def run_async(self):
        threading.Thread(target=self._read_async).start()

    def _send_packet(self, packet):
        print "%s:%s => %s" % (self.host, self.port, json.dumps(packet, indent=4))

        raw = json.dumps(packet).encode("zlib")
        self.output.write(PacketManager.SIZE_PACK.pack(len(raw)))
        self.output.write(raw)

    def _recieve_packet(self, packet):
        print "%s:%s <= %s" % (self.host, self.port, json.dumps(packet, indent=4))

        name = packet["name"]
        if name == "submission-request":
            self.judge.current_submission = packet["submission-id"]
            self.judge.begin_grading(packet["problem-id"], packet["language"], packet["source"])
        elif name == "get-current-submission":
            self.current_submission_packet()
        else:
            print "ERROR: unknown packet %s, payload %s" % (name, packet)

    def test_case_status_packet(self, position, points, total_points, status, time, memory, output):
        self._send_packet({"name": "test-case-status",
                           "submission-id": self.judge.current_submission,
                           "position": position,
                           "status": status,
                           "time": time,
                           "points": points,
                           "total-points": total_points,
                           "memory": memory,
                           "output": output})

    def compile_error_packet(self, log):
        self._send_packet({"name": "compile-error",
                           "submission-id": self.judge.current_submission,
                           "log": log})

    def begin_grading_packet(self):
        self._send_packet({"name": "grading-begin",
                           "submission-id": self.judge.current_submission})

    def grading_end_packet(self):
        self._send_packet({"name": "grading-end",
                           "submission-id": self.judge.current_submission})
        self.judge.current_submission = None

    def current_submission_packet(self):
        self._send_packet({"name": "current-submission-id",
                           "submission-id": self.judge.current_submission})
