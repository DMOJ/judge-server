import sys

execute = None

if "nix" in sys.platform or "linux" in sys.platform:
    import nix_execute
    execute = nix_execute.execute
elif sys.platform == "win32":
    import win_execute
    execute = win_execute.execute
else:
    raise Exception("execution not implemented for %s" % sys.platform)