import os
from enum import Enum
from typing import Sequence, Union


class AccessMode(Enum):
    NONE = 0
    EXACT = 1
    RECURSIVE = 2

    # flake8 doesn't recognize `AccessMode` in type annotations here
    @classmethod
    def more_permissive(cls, mode1, mode2):
        return cls(max(mode1.value, mode2.value))


class Dir:
    def __init__(self):
        self.access_mode = AccessMode.NONE
        self.subpath_map = {}


class File:
    pass


class BaseFilesystemAccessRule:
    def __init__(self, path: str):
        path = os.path.expanduser(path)
        assert os.path.abspath(path) == path, 'FilesystemAccessRule must specify a normalized, absolute path to rule'
        self.path = path
        self._assert_rule_type()

    def _assert_rule_type(self) -> None:
        if self.exists():
            self._assert_dir_type(os.path.isdir(self.path))

    def _assert_dir_type(self, is_dir: bool) -> None:
        raise NotImplementedError

    def exists(self):
        return os.path.exists(self.path)

    def realpath(self):
        return os.path.realpath(self.path)

    def is_realpath(self) -> bool:
        return self.path.startswith('/proc/self') or self.realpath() == self.path  # proc/self should not be resolved

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} {self.path}>'


class ExactFile(BaseFilesystemAccessRule):
    def _assert_dir_type(self, is_dir: bool) -> None:
        assert not is_dir, f"Can't apply file rule to directory {self.path}"


class DirFilesystemAccessRule(BaseFilesystemAccessRule):
    def _assert_dir_type(self, is_dir: bool) -> None:
        assert is_dir, f"Can't apply directory rule to non-directory {self.path}"


class ExactDir(DirFilesystemAccessRule):
    access_mode = AccessMode.EXACT


class RecursiveDir(DirFilesystemAccessRule):
    access_mode = AccessMode.RECURSIVE


# Mainly for MyPy: only ExactFile, ExactDir and RecursiveDir are to be considered rules
FilesystemAccessRule = Union[ExactFile, ExactDir, RecursiveDir]


class FilesystemPolicy:
    def __init__(self, rules: Sequence[FilesystemAccessRule]):
        self.root = Dir()
        for rule in rules:
            self._add_rule(rule)

    def _add_rule(self, rule: FilesystemAccessRule) -> None:
        if not rule.exists():
            return

        if rule.path == '/':
            return self._finalize_root_rule(rule)

        *directory_path, final_component = rule.path.split('/')[1:]

        node = self.root
        for component in directory_path:
            new_node = node.subpath_map.setdefault(component, Dir())
            assert isinstance(new_node, Dir), 'Cannot add rule: refusing to descend into non-directory'
            node = new_node

        self._finalize_rule(node, final_component, rule)

        # Add symlink targets too
        if not rule.is_realpath():
            self._add_rule(type(rule)(rule.realpath()))

    def _finalize_root_rule(self, rule: FilesystemAccessRule) -> None:
        assert not isinstance(rule, ExactFile), 'Root is not a file'
        self._finalize_directory_rule(self.root, rule)

    def _finalize_rule(self, node: Dir, final_component: str, rule: FilesystemAccessRule) -> None:
        assert final_component != '', 'Must not have trailing slashes in rule path'
        if isinstance(rule, ExactFile):
            new_node = node.subpath_map.setdefault(final_component, File())
            assert isinstance(new_node, File), "Can't add ExactFile: Dir rule exists"
        else:
            new_node = node.subpath_map.setdefault(final_component, Dir())
            assert isinstance(new_node, Dir), "Can't add rule: File rule exists"
            self._finalize_directory_rule(new_node, rule)

    def _finalize_directory_rule(self, node: Dir, rule: Union[ExactDir, RecursiveDir]) -> None:
        node.access_mode = AccessMode.more_permissive(
            node.access_mode, rule.access_mode
        )  # Allow the more permissive rule

    # `path` should be a normalized path
    def check(self, path: str) -> bool:
        assert os.path.abspath(path) == path, 'Must pass a normalized, absolute path to check'
        components = [] if path == '/' else path.split('/')[1:]

        node = self.root
        for component in components:
            if isinstance(node, File):
                return False
            elif node.access_mode == AccessMode.RECURSIVE:
                return True
            else:
                node = node.subpath_map.get(component)
                if node is None:
                    return False

        return self._check_final_node(node)

    def _check_final_node(self, node: Union[Dir, File]) -> bool:
        return isinstance(node, File) or node.access_mode != AccessMode.NONE
