from dmoj.executors.script_executor import ScriptExecutor


class Executor(ScriptExecutor):
    name = 'LOLCODE'
    ext = '.lic'
    command = 'lci'
    command_paths = ['lci']

    test_program = '''\
HAI 1.2
    CAN HAS STDIO?
    I HAS A INPUT
    GIMMEH INPUT
    VISIBLE INPUT
KTHXBYE
'''

    def get_cmdline(self, **kwargs):
        return ['lci', self._code]
