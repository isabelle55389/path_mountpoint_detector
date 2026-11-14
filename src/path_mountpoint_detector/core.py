"""Determine whether a path is a mountpoint by comparing device and inode
with its parent directory.

The classic POSIX trick is: a directory is a mountpoint iff
``stat(path).st_dev != stat(parent).st_dev`` OR
``stat(path).st_ino == stat(parent).st_ino``.  The inode check catches
bind mounts and other cases where the device number is unchanged but the
directory tree is a different view of the same underlying inode.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MountInfo:
    """Result of inspecting a path for mountpoint-ness.

    ``path`` is the path as given by the caller (not resolved).
    ``resolved`` is the fully resolved absolute path that was stat'd.
    ``is_mountpoint`` is the verdict.
    ``device`` and ``inode`` are the stat values of the resolved path.
    ``parent_device`` and ``parent_inode`` are the stat values of the
    resolved path's parent directory.
    """

    path: str
    resolved: str
    is_mountpoint: bool
    device: int
    inode: int
    parent_device: int
    parent_inode: int


def mountpoint_info(path: str) -> MountInfo:
    """Inspect ``path`` and report whether it is a mountpoint.

    The path is resolved with :func:`os.path.realpath` first so that
    symlinks do not confuse the comparison (a symlink to a mountpoint is
    not itself a mountpoint, and a mountpoint reached through a symlink
    should still be detected).

    Raises :class:`FileNotFoundError` if the path does not exist, and
    :class:`NotADirectoryError` if the resolved path is not a directory.
    The root directory ``/`` is special-cased: it has no distinct parent
    inode to compare against, so it is always considered a mountpoint.
    """
    resolved = os.path.realpath(path)
    st = os.stat(resolved)
    if not os.path.isdir(resolved):
        raise NotADirectoryError(path)

    if resolved == os.path.sep:
        # The root has no parent we can meaningfully compare against;
        # by definition it is the root of the filesystem tree and is
        # treated as a mountpoint.
        return MountInfo(
            path=path,
            resolved=resolved,
            is_mountpoint=True,
            device=st.st_dev,
            inode=st.st_ino,
            parent_device=st.st_dev,
            parent_inode=st.st_ino,
        )

    parent = os.path.dirname(resolved)
    pst = os.stat(parent)

    # A directory is a mountpoint when its device differs from its parent
    # (a classic mount) OR when its inode equals its parent's inode (a
    # bind mount or a stacked view that shares the same inode).
    is_mp = (st.st_dev != pst.st_dev) or (st.st_ino == pst.st_ino)

    return MountInfo(
        path=path,
        resolved=resolved,
        is_mountpoint=is_mp,
        device=st.st_dev,
        inode=st.st_ino,
        parent_device=pst.st_dev,
        parent_inode=pst.st_ino,
    )


def is_mountpoint(path: str) -> bool:
    """Return ``True`` if ``path`` is a mountpoint, ``False`` otherwise.

    Thin wrapper around :func:`mountpoint_info` for callers that only
    need the boolean answer.  Raises the same exceptions as
    :func:`mountpoint_info` for missing paths and non-directories.
    """
    return mountpoint_info(path).is_mountpoint
