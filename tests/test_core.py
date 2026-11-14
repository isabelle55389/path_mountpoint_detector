import os
import tempfile
import unittest

from path_mountpoint_detector import MountInfo, is_mountpoint, mountpoint_info


class TestMountpointInfo(unittest.TestCase):
    def test_root_is_mountpoint(self):
        info = mountpoint_info(os.path.sep)
        self.assertTrue(info.is_mountpoint)
        self.assertEqual(info.resolved, os.path.sep)

    def test_is_mountpoint_root(self):
        self.assertTrue(is_mountpoint(os.path.sep))

    def test_regular_directory_is_not_mountpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            sub = os.path.join(tmp, "inner")
            os.mkdir(sub)
            info = mountpoint_info(sub)
            self.assertFalse(info.is_mountpoint)
            self.assertEqual(info.device, info.parent_device)
            self.assertNotEqual(info.inode, info.parent_inode)

    def test_returns_mountinfo_instance(self):
        with tempfile.TemporaryDirectory() as tmp:
            info = mountpoint_info(tmp)
            self.assertIsInstance(info, MountInfo)
            self.assertEqual(info.path, tmp)
            self.assertEqual(info.resolved, os.path.realpath(tmp))

    def test_missing_path_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = os.path.join(tmp, "does-not-exist")
            with self.assertRaises(FileNotFoundError):
                mountpoint_info(missing)

    def test_regular_file_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = os.path.join(tmp, "file.txt")
            with open(f, "w") as fh:
                fh.write("x")
            with self.assertRaises(NotADirectoryError):
                mountpoint_info(f)

    def test_symlink_to_regular_dir_is_not_mountpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "target")
            os.mkdir(target)
            link = os.path.join(tmp, "link")
            os.symlink(target, link)
            # Resolving the symlink lands on a plain directory, so the
            # verdict must be False even though the link itself has a
            # different inode from its parent.
            self.assertFalse(is_mountpoint(link))

    def test_resolved_path_is_absolute(self):
        with tempfile.TemporaryDirectory() as tmp:
            info = mountpoint_info(tmp)
            self.assertTrue(os.path.isabs(info.resolved))

    def test_parent_fields_are_ints(self):
        with tempfile.TemporaryDirectory() as tmp:
            info = mountpoint_info(tmp)
            self.assertIsInstance(info.device, int)
            self.assertIsInstance(info.inode, int)
            self.assertIsInstance(info.parent_device, int)
            self.assertIsInstance(info.parent_inode, int)

    def test_bind_mount_inode_rule(self):
        # We cannot create a real bind mount without privileges, but we
        # can verify the rule the implementation claims to use by
        # checking the two conditions directly on a normal directory.
        with tempfile.TemporaryDirectory() as tmp:
            info = mountpoint_info(tmp)
            expected = (info.device != info.parent_device) or (
                info.inode == info.parent_inode
            )
            self.assertEqual(info.is_mountpoint, expected)

    def test_trailing_slash_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            info = mountpoint_info(tmp + os.sep)
            self.assertFalse(info.is_mountpoint)
            self.assertEqual(info.resolved, os.path.realpath(tmp))


if __name__ == "__main__":
    unittest.main()
