from http.server import BaseHTTPRequestHandler


class JudgeControlRequestHandler(BaseHTTPRequestHandler):
    judge = None

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
        self.send_error(404)
