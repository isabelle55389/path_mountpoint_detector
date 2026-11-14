# path_mountpoint_detector

Determines whether a given path is a mountpoint by comparing its device and
inode against its parent directory.

## Usage

```python
from path_mountpoint_detector import is_mountpoint, mountpoint_info

is_mountpoint("/")            # True
is_mountpoint("/tmp")         # usually False

info = mountpoint_info("/")
print(info.is_mountpoint)     # True
print(info.device, info.inode)
```

Exported names: `is_mountpoint(path) -> bool`, `mountpoint_info(path) -> MountInfo`,
and the `MountInfo` dataclass with fields `path`, `resolved`, `is_mountpoint`,
`device`, `inode`, `parent_device`, `parent_inode`.

## Why this exists

The kernel exposes mount information in `/proc/self/mountinfo`, but parsing that
file is awkward and racy, and it requires a Linux-specific format. The classic
POSIX alternative is to `stat` a path and its parent and compare `st_dev` and
`st_ino`. That is what this library does: no third-party dependencies, no
subprocesses, no parsing of `/proc`.

The rule implemented is: a directory is a mountpoint if its device number
differs from its parent's, **or** if its inode number equals its parent's.
The second condition catches bind mounts and stacked views where the device
number is unchanged but the directory is a different view of the same inode.

## The awkward edge

The path is resolved with `os.path.realpath` before comparing. A symlink that
points at a mountpoint is therefore reported as a mountpoint (the resolved
target is one), and a symlink that points at a plain directory is reported as
not a mountpoint (the resolved target is not one). If you want to know about
the symlink itself rather than its target, stat the link directly; that is a
different question and this library deliberately answers the resolved one.

The root directory `/` is always reported as a mountpoint. It has no distinct
parent inode to compare against, and treating it as a mountpoint matches the
intuition that the filesystem tree has to be mounted somewhere. Non-existent
paths raise `FileNotFoundError`; paths that resolve to non-directories raise
`NotADirectoryError`.
