import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from core import process


class ProcessStartTests(unittest.TestCase):

    def test_start_process_uses_explicit_file_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "demo.py")
            with open(file_path, "w", encoding="utf-8") as handle:
                handle.write("print('hello')\n")

            with patch("core.process.PtyProcess.spawn") as spawn_mock, patch(
                "core.process.update_file_status_by_filename"
            ):
                spawn_mock.return_value = SimpleNamespace(isalive=lambda: False)
                success, message = process.start_process("demo.py", file_path=file_path)

            self.assertTrue(success)
            self.assertIn("started successfully", message.lower())
            self.assertEqual(spawn_mock.call_args.args[0][2], file_path)


if __name__ == "__main__":
    unittest.main()
