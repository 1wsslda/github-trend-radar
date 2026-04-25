from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gitsonar.runtime.settings import make_settings_runtime
from gitsonar.runtime.utils import as_bool, clamp_int, normalize, normalize_proxy_url, parse_proxy_endpoint


class _DummySession:
    def __init__(self):
        self.headers: dict[str, str] = {}
        self.proxies: dict[str, str] = {}


class RuntimeSettingsTests(unittest.TestCase):
    def build_runtime(
        self,
        settings: dict[str, object],
        tempdir: str,
        *,
        session: _DummySession | None = None,
        translate_session: _DummySession | None = None,
        detect_local_proxy=None,
    ):
        settings_path = Path(tempdir) / "settings.json"
        return make_settings_runtime(
            settings=settings,
            settings_path=str(settings_path),
            runtime_root=tempdir,
            session=session or _DummySession(),
            translate_session=translate_session or _DummySession(),
            current_port_getter=lambda: 8080,
            runtime_port_getter=lambda: 8080,
            normalize=normalize,
            clamp_int=clamp_int,
            as_bool=as_bool,
            decrypt_secret=lambda value: str(value or "")[4:] if str(value or "").startswith("enc:") else str(value or ""),
            encrypt_secret=lambda value: f"enc:{value}" if value else "",
            normalize_proxy_url=normalize_proxy_url,
            parse_proxy_endpoint=parse_proxy_endpoint,
            detect_local_proxy=detect_local_proxy or (lambda skip=None: "" if skip else "http://127.0.0.1:7897"),
            tcp_port_open=lambda _host, _port: True,
            load_json_file=lambda path, default: json.loads(Path(path).read_text(encoding="utf-8")) if Path(path).exists() else default,
            atomic_write_json=lambda path, payload: Path(path).write_text(json.dumps(payload), encoding="utf-8"),
        )

    def test_merge_settings_keeps_existing_sensitive_values_on_blank_input(self):
        with tempfile.TemporaryDirectory() as tempdir:
            settings = {
                "port": 8080,
                "refresh_hours": 1,
                "result_limit": 25,
                "default_sort": "stars",
                "auto_start": False,
                "github_token": "saved-token",
                "proxy": "http://127.0.0.1:7890",
            }
            runtime = self.build_runtime(settings, tempdir)

            merged = runtime.merge_settings(
                {
                    "github_token": "",
                    "proxy": "",
                    "refresh_hours": 2,
                    "result_limit": 40,
                },
                settings,
            )

            self.assertEqual(merged["github_token"], "saved-token")
            self.assertEqual(merged["proxy"], "http://127.0.0.1:7890")
            self.assertEqual(merged["refresh_hours"], 2)
            self.assertEqual(merged["result_limit"], 40)

    def test_merge_settings_clear_flags_remove_sensitive_values(self):
        with tempfile.TemporaryDirectory() as tempdir:
            settings = {
                "port": 8080,
                "refresh_hours": 1,
                "result_limit": 25,
                "default_sort": "stars",
                "auto_start": False,
                "github_token": "saved-token",
                "proxy": "http://127.0.0.1:7890",
            }
            runtime = self.build_runtime(settings, tempdir)

            merged = runtime.merge_settings(
                {
                    "clear_github_token": True,
                    "clear_proxy": True,
                },
                settings,
            )

            self.assertEqual(merged["github_token"], "")
            self.assertEqual(merged["proxy"], "")

    def test_sanitize_settings_preserves_legacy_shape_with_safe_sensitive_placeholders(self):
        with tempfile.TemporaryDirectory() as tempdir:
            settings = {
                "port": 8080,
                "refresh_hours": 1,
                "result_limit": 25,
                "default_sort": "stars",
                "auto_start": False,
                "github_token": "saved-token",
                "proxy": "",
            }
            runtime = self.build_runtime(settings, tempdir)
            runtime.apply_runtime_settings()

            payload = runtime.sanitize_settings(True)

            self.assertTrue(payload["has_github_token"])
            self.assertFalse(payload["has_proxy"])
            self.assertEqual(payload["effective_proxy"], "http://127.0.0.1:7897")
            self.assertEqual(payload["proxy_source"], "auto")
            self.assertEqual(payload["github_token"], "")
            self.assertEqual(payload["proxy"], "")
            self.assertEqual(payload["runtime_root"], "")
            self.assertEqual(payload["translation_provider"], "google")
            self.assertEqual(payload["translation_api_endpoint"], "")
            self.assertEqual(payload["translation_api_model"], "")
            self.assertFalse(payload["has_translation_api_key"])
            self.assertNotIn("translation_api_key", payload)

    def test_merge_settings_accepts_openai_compatible_https_endpoint_and_api_key(self):
        with tempfile.TemporaryDirectory() as tempdir:
            settings = {
                "port": 8080,
                "refresh_hours": 1,
                "result_limit": 25,
                "default_sort": "stars",
                "auto_start": False,
                "github_token": "",
                "proxy": "",
            }
            runtime = self.build_runtime(settings, tempdir)

            merged = runtime.merge_settings(
                {
                    "translation_provider": "openai_compatible",
                    "translation_api_endpoint": "https://api.example.test/v1/chat/completions",
                    "translation_api_model": "gpt-4o-mini",
                    "translation_api_key": "test-key",
                },
                settings,
            )

            self.assertEqual(merged["translation_provider"], "openai_compatible")
            self.assertEqual(merged["translation_api_endpoint"], "https://api.example.test/v1/chat/completions")
            self.assertEqual(merged["translation_api_model"], "gpt-4o-mini")
            self.assertEqual(merged["translation_api_key"], "test-key")

    def test_merge_settings_rejects_remote_http_translation_api_endpoint(self):
        with tempfile.TemporaryDirectory() as tempdir:
            runtime = self.build_runtime({}, tempdir)

            with self.assertRaisesRegex(ValueError, "翻译 API Endpoint"):
                runtime.merge_settings(
                    {
                        "translation_provider": "openai_compatible",
                        "translation_api_endpoint": "http://api.example.test/v1/chat/completions",
                        "translation_api_model": "gpt-4o-mini",
                    },
                    {},
                )

    def test_merge_settings_accepts_loopback_http_translation_api_endpoint(self):
        with tempfile.TemporaryDirectory() as tempdir:
            runtime = self.build_runtime({}, tempdir)

            merged = runtime.merge_settings(
                {
                    "translation_provider": "openai_compatible",
                    "translation_api_endpoint": "http://127.0.0.1:8081/v1/chat/completions",
                    "translation_api_model": "local-model",
                },
                {},
            )

            self.assertEqual(merged["translation_api_endpoint"], "http://127.0.0.1:8081/v1/chat/completions")
            self.assertEqual(merged["translation_api_model"], "local-model")

    def test_save_settings_encrypts_translation_api_key_and_sanitize_does_not_leak_it(self):
        with tempfile.TemporaryDirectory() as tempdir:
            settings = {
                "port": 8080,
                "refresh_hours": 1,
                "result_limit": 25,
                "default_sort": "stars",
                "auto_start": False,
                "github_token": "",
                "proxy": "",
                "translation_provider": "openai_compatible",
                "translation_api_endpoint": "https://api.example.test/v1/chat/completions",
                "translation_api_model": "gpt-4o-mini",
                "translation_api_key": "test-key",
            }
            runtime = self.build_runtime(settings, tempdir)
            runtime.save_settings(settings)

            saved = json.loads((Path(tempdir) / "settings.json").read_text(encoding="utf-8"))
            payload = runtime.sanitize_settings(True)
            payload_text = json.dumps(payload, ensure_ascii=False)

            self.assertEqual(saved["translation_api_key"], "enc:test-key")
            self.assertTrue(payload["has_translation_api_key"])
            self.assertNotIn("translation_api_key", payload)
            self.assertNotIn("test-key", payload_text)

    def test_save_settings_encrypts_token_without_affecting_proxy_metadata(self):
        with tempfile.TemporaryDirectory() as tempdir:
            settings = {
                "port": 8080,
                "refresh_hours": 1,
                "result_limit": 25,
                "default_sort": "stars",
                "auto_start": False,
                "github_token": "saved-token",
                "proxy": "http://127.0.0.1:7890",
            }
            runtime = self.build_runtime(settings, tempdir)
            runtime.save_settings(settings)

            saved = json.loads((Path(tempdir) / "settings.json").read_text(encoding="utf-8"))

            self.assertEqual(saved["github_token"], "enc:saved-token")
            self.assertEqual(saved["proxy"], "http://127.0.0.1:7890")

    def test_save_settings_encrypts_proxy_credentials_while_preserving_runtime_value(self):
        with tempfile.TemporaryDirectory() as tempdir:
            settings = {
                "port": 8080,
                "refresh_hours": 1,
                "result_limit": 25,
                "default_sort": "stars",
                "auto_start": False,
                "github_token": "saved-token",
                "proxy": "http://user:pass@127.0.0.1:7890",
            }
            runtime = self.build_runtime(settings, tempdir)
            runtime.save_settings(settings)

            saved = json.loads((Path(tempdir) / "settings.json").read_text(encoding="utf-8"))

            self.assertEqual(saved["github_token"], "enc:saved-token")
            self.assertEqual(saved["proxy"], "enc:http://user:pass@127.0.0.1:7890")
            self.assertEqual(settings["proxy"], "http://user:pass@127.0.0.1:7890")

    def test_load_settings_reads_legacy_plaintext_proxy_with_credentials(self):
        with tempfile.TemporaryDirectory() as tempdir:
            settings_file = Path(tempdir) / "settings.json"
            settings_file.write_text(
                json.dumps(
                    {
                        "port": 8080,
                        "refresh_hours": 1,
                        "result_limit": 25,
                        "default_sort": "stars",
                        "auto_start": False,
                        "github_token": "",
                        "proxy": "http://user:pass@127.0.0.1:7890",
                    }
                ),
                encoding="utf-8",
            )
            runtime = self.build_runtime({}, tempdir)

            loaded = runtime.load_settings()

            self.assertEqual(loaded["proxy"], "http://user:pass@127.0.0.1:7890")

    def test_load_settings_decrypts_encrypted_proxy_with_credentials(self):
        with tempfile.TemporaryDirectory() as tempdir:
            settings_file = Path(tempdir) / "settings.json"
            settings_file.write_text(
                json.dumps(
                    {
                        "port": 8080,
                        "refresh_hours": 1,
                        "result_limit": 25,
                        "default_sort": "stars",
                        "auto_start": False,
                        "github_token": "",
                        "proxy": "enc:http://user:pass@127.0.0.1:7890",
                    }
                ),
                encoding="utf-8",
            )
            runtime = self.build_runtime({}, tempdir)

            loaded = runtime.load_settings()

            self.assertEqual(loaded["proxy"], "http://user:pass@127.0.0.1:7890")

    def test_sanitize_settings_redacts_effective_proxy_credentials_and_runtime_root(self):
        with tempfile.TemporaryDirectory() as tempdir:
            session = _DummySession()
            translate_session = _DummySession()
            settings = {
                "port": 8080,
                "refresh_hours": 1,
                "result_limit": 25,
                "default_sort": "stars",
                "auto_start": False,
                "github_token": "",
                "proxy": "http://user:pass@127.0.0.1:7890",
            }
            runtime = self.build_runtime(settings, tempdir, session=session, translate_session=translate_session)

            runtime.apply_runtime_settings()
            payload = runtime.sanitize_settings(True)
            payload_text = json.dumps(payload, ensure_ascii=False)

            self.assertEqual(session.proxies["http"], "http://user:pass@127.0.0.1:7890")
            self.assertEqual(translate_session.proxies["https"], "http://user:pass@127.0.0.1:7890")
            self.assertEqual(payload["effective_proxy"], "http://***:***@127.0.0.1:7890")
            self.assertNotIn("user:pass", payload_text)
            self.assertNotIn(tempdir, payload_text)
            self.assertEqual(payload.get("runtime_root", ""), "")


if __name__ == "__main__":
    unittest.main()
