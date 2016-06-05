import os

if os.name == 'posix':
    from .nix import signal_debugger
else:
    from .win import ctrl_debugger