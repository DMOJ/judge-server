import sys

execute = None

if "nix" in sys.platform or "linux" in sys.platform:
    import nix_execute
    execute = nix_execute.execute
else:
    raise Exception("execution not implemented for %s" % sys.platform)