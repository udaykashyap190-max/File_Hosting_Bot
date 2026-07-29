import unittest
from unittest.mock import patch

from core import auth


class AuthAccessTests(unittest.TestCase):

    def test_has_access_allows_approved_users(self):
        with patch("core.auth.is_admin", return_value=False), patch(
            "core.auth.get_user_status", return_value="approved"
        ):
            self.assertTrue(auth.has_access(12345))

    def test_has_access_blocks_pending_users(self):
        with patch("core.auth.is_admin", return_value=False), patch(
            "core.auth.get_user_status", return_value="pending"
        ):
            self.assertFalse(auth.has_access(12345))


if __name__ == "__main__":
    unittest.main()
