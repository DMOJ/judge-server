import os

if os.name == 'posix':
    from .nix.signal_debugger import setup_all_debuggers
else:
    from .win.ctrl_debugger import setup_all_debuggers