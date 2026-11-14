"""Public API for path_mountpoint_detector."""

from .core import is_mountpoint, mountpoint_info, MountInfo

__all__ = ["is_mountpoint", "mountpoint_info", "MountInfo"]
