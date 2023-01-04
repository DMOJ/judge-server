import glob
from pathlib import Path


def find_glob_root(g: str) -> Path:
    """
    Given a glob, find a directory that contains all its possible patterns
    """
    dir = Path(g)
    while str(dir) != glob.escape(str(dir)):
        dir = dir.parent
    return dir
