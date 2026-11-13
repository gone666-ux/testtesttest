import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import main as entry

PROJECT_ROOT = Path(__file__).resolve().parent
MAIN_PATH = PROJECT_ROOT / "main.py"
EXPECTED_BYTES = b"I asked my AI coding agent to fix a typo; it rewrote 40 files, including the ticket, which now says 'rewrite 40 files.'"
EXPECTED_SHA256 = "3129267db67f71ba39f51ad290cd3eaeeedb1c80cc86f50a50b074c8ca714c00"


class EntryTests(unittest.TestCase):
    def test_expected_bytes_and_hash(self):
        self.assertEqual(
            EXPECTED_BYTES.decode("utf-8"),
            "I asked my AI coding agent to fix a typo; it rewrote 40 files, including the ticket, which now says 'rewrite 40 files.'",
        )
        self.assertEqual(hashlib.sha256(EXPECTED_BYTES).hexdigest(), EXPECTED_SHA256)

    def test_written_file_is_exact(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = entry.write_entry(Path(tmp))
            data = path.read_bytes()
            self.assertEqual(path, Path(tmp) / "entry.txt")
            self.assertEqual(data, EXPECTED_BYTES)
            self.assertEqual(hashlib.sha256(data).hexdigest(), EXPECTED_SHA256)
            self.assertFalse(data.endswith(b"\n"))
            text = data.decode("utf-8")
            self.assertGreaterEqual(len(text), 1)
            self.assertLessEqual(len(text), 280)
            self.assertTrue(any(not char.isspace() for char in text))

    def test_repeated_runs_are_byte_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = entry.write_entry(Path(tmp, "first")).read_bytes()
            second = entry.write_entry(Path(tmp, "second")).read_bytes()
            self.assertEqual(first, second)
            self.assertEqual(first, EXPECTED_BYTES)

    def test_replaces_stale_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            (output_dir / "entry.txt").write_bytes(b"stale contents\n")
            path = entry.write_entry(output_dir)
            self.assertEqual(path.read_bytes(), EXPECTED_BYTES)

    def test_creates_missing_nested_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp, "missing", "deeper", "output")
            self.assertFalse(output_dir.exists())
            path = entry.write_entry(output_dir)
            self.assertTrue(output_dir.is_dir())
            self.assertEqual(path.read_bytes(), EXPECTED_BYTES)

    def test_import_has_no_filesystem_side_effects(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(
                os.environ,
                PYTHONPATH=str(PROJECT_ROOT),
                PYTHONDONTWRITEBYTECODE="1",
            )
            env.pop("MAKEFUN_OUTPUT_DIR", None)
            result = subprocess.run(
                [sys.executable, "-c", "import main"],
                cwd=tmp,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_default_output_dir_uses_writer(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(entry, "write_entry") as writer:
                entry.main()
        writer.assert_called_once_with(Path("/output"))

    def test_environment_output_dir_uses_writer(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {"MAKEFUN_OUTPUT_DIR": tmp}, clear=True):
                with mock.patch.object(entry, "write_entry") as writer:
                    entry.main()
            writer.assert_called_once_with(Path(tmp))

    def test_subprocess_with_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp, "nested", "out")
            env = dict(os.environ, MAKEFUN_OUTPUT_DIR=str(output_dir))
            result = subprocess.run(
                [sys.executable, str(MAIN_PATH)],
                cwd=tmp,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            data = (output_dir / "entry.txt").read_bytes()
            self.assertEqual(data, EXPECTED_BYTES)
            self.assertFalse(data.endswith(b"\n"))


if __name__ == "__main__":
    unittest.main()
