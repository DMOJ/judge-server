import threading
import unittest
from http.server import HTTPServer
from unittest import mock

import requests

from dmoj.control import JudgeControlRequestHandler


class ControlServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class FakeJudge:
            pass

        class Handler(JudgeControlRequestHandler):
            judge = FakeJudge()

        cls.judge = Handler.judge
        cls.server = HTTPServer(('127.0.0.1', 0), Handler)

        cls.server_thread = threading.Thread(target=cls.server.serve_forever)
        cls.server_thread.start()

        cls.connect = 'http://%s:%s/' % cls.server.server_address

    def setUp(self):
        self.update_mock = self.judge.update_problems = mock.Mock()

    def test_get_404(self):
        self.assertEqual(requests.get(self.connect).status_code, 404)
        self.assertEqual(requests.get(self.connect + 'update/problems').status_code, 404)
        self.update_mock.assert_not_called()

    def test_post_404(self):
        self.assertEqual(requests.post(self.connect).status_code, 404)
        self.update_mock.assert_not_called()

    def test_update_problem(self):
        requests.post(self.connect + 'update/problems')
        self.update_mock.assert_called_with()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server_thread.join()
        cls.server.server_close()
