from __future__ import annotations

import base64
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import gitsonar.runtime.utils as runtime_utils
from gitsonar.runtime.utils import decrypt_secret, encrypt_secret, load_json_file


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

    def test_dpapi_encrypt_and_decrypt_forbid_system_ui(self):
        calls: list[tuple[str, int]] = []

        class FakeCrypt32:
            def CryptProtectData(self, *_args):
                calls.append(("protect", _args[5]))
                return True

            def CryptUnprotectData(self, *_args):
                calls.append(("unprotect", _args[5]))
                return True

        fake_windll = SimpleNamespace(
            crypt32=FakeCrypt32(),
            kernel32=SimpleNamespace(LocalFree=lambda _ptr: None),
        )
        ciphertext = "dpapi:" + base64.b64encode(b"ciphertext").decode("ascii")

        with (
            patch.object(runtime_utils.os, "name", "nt"),
            patch.object(runtime_utils.ctypes, "windll", fake_windll, create=True),
            patch.object(runtime_utils.ctypes, "string_at", return_value=b"secret"),
        ):
            encrypted = encrypt_secret("secret")
            decrypted = decrypt_secret(ciphertext)

        self.assertTrue(encrypted.startswith("dpapi:"))
        self.assertEqual(decrypted, "secret")
        self.assertEqual(calls, [("protect", 0x1), ("unprotect", 0x1)])


if __name__ == "__main__":
    unittest.main()
