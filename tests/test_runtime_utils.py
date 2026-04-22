from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gitsonar.runtime.utils import load_json_file


class RuntimeUtilsTests(unittest.TestCase):
    def test_load_json_file_returns_default_without_logging_for_missing_file(self):
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "missing.json"
            with self.assertNoLogs("gitsonar.runtime.utils", level="WARNING"):
                payload = load_json_file(str(path), {"fallback": True})
            self.assertEqual(payload, {"fallback": True})

    def test_load_json_file_accepts_utf8_bom(self):
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "bom.json"
            path.write_text('{"label":"中文"}', encoding="utf-8-sig")
            with self.assertNoLogs("gitsonar.runtime.utils", level="WARNING"):
                payload = load_json_file(str(path), {"fallback": True})
            self.assertEqual(payload, {"label": "中文"})

    def test_load_json_file_logs_warning_and_returns_default_for_invalid_json(self):
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "broken.json"
            path.write_text("{not-json", encoding="utf-8")
            with self.assertLogs("gitsonar.runtime.utils", level="WARNING") as captured:
                payload = load_json_file(str(path), {"fallback": True})
            self.assertEqual(payload, {"fallback": True})
            self.assertIn("broken.json", captured.output[0])
            self.assertIn("json_load_failed", captured.output[0])


if __name__ == "__main__":
    unittest.main()
