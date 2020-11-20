import os
from hashlib import md5

import requests
from requests.exceptions import RequestException
import yaml
from yaml.parser import ParserError
from yaml.scanner import ScannerError

from dmoj.config import ConfigNode, InvalidInitException
from dmoj.judgeenv import get_problem_roots
from dmoj.problem import Problem

import re

regex = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)


class RemoteProblem(Problem):

    def __init__(self, problem_config: str, time_limit, memory_limit, meta):
        # config 改变时问题目录也会改变，所有的文件会重新下载
        self.problem_id = md5(problem_config.encode()).hexdigest()
        self.time_limit = time_limit
        self.memory_limit = memory_limit
        self.meta = ConfigNode(meta)
        root_dir = get_problem_roots()[0]
        self.root_dir = os.path.join(root_dir, self.problem_id)
        self._checkers = {}
        try:
            doc = yaml.safe_load(problem_config)
            doc = self.replace_url_to_file(doc)
            self.config = ConfigNode(
                doc,
                defaults={
                    'wall_time_factor': 3,
                    'output_prefix_length': 0 if 'signature_grader' in doc else 64,
                    'output_limit_length': 25165824,
                    'binary_data': False,
                    'short_circuit': True,
                    'points': 1,
                    'symlinks': {},
                    'meta': meta,
                },
            )
        except (IOError, KeyError, ParserError, ScannerError, RequestException) as e:
            raise InvalidInitException(str(e))
        self._resolve_test_cases()

    def replace_url_to_file(self, doc):
        for i, item in enumerate(doc['test_cases']):
            if regex.match(item['in']):
                file_name = os.path.join(self.root_dir, f'{i}.in')
                if not os.path.isfile(file_name):
                    resp = requests.get(item['in'], timeout=3)
                    with open(file_name, 'rb') as f:
                        f.write(resp.content)
                item['in'] = file_name
            if regex.match(item['out']):
                file_name = os.path.join(self.root_dir, f'{i}.out')
                if not os.path.isfile(file_name):
                    resp = requests.get(item['out'], timeout=3)
                    with open(file_name, 'rb') as f:
                        f.write(resp.content)
                item['out'] = file_name
        return doc
