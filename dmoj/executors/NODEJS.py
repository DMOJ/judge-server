from dmoj.cptbox.filesystem_policies import ExactFile
from dmoj.executors.script_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = 'js'
    command = 'node'
    nproc = -1
    command_paths = ['node', 'nodejs']
    syscalls = [
        'capget',
        'eventfd2',
        'shutdown',
        'pkey_alloc',
        'pkey_free',
    ]
    address_grace = 1048576
    test_program = """
process.stdin.on('readable', () => {
    const chunk = process.stdin.read();
    if (chunk != null) {
        process.stdout.write(chunk);
    }
});
"""

    def get_env(self):
        env = super().get_env()
        # Disable io_uring due to potential security implications
        env['UV_USE_IO_URING'] = '0'
        return env

    def get_fs(self):
        return super().get_fs() + [ExactFile('/usr/lib/ssl/openssl.cnf')]

    @classmethod
    def get_version_flags(cls, command):
        return ['--version']
