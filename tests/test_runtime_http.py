from __future__ import annotations

import http.client
import json
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gitsonar.runtime.http import make_app_handler
from gitsonar.runtime.utils import as_bool, clamp_int, normalize


class RuntimeHTTPHandlerTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        runtime_root = Path(self.tempdir.name)
        self.runtime_root = runtime_root
        (runtime_root / "trending.html").write_text("<html>ok</html>", encoding="utf-8")
        self.control_token = "runtime-control-token"
        self.state_updates: list[tuple[str, bool, dict[str, object] | None]] = []
        self.exit_requested = False
        self.refresh_started = True
        self.validated_tokens: list[object | None] = []
        self.saved_settings: list[dict[str, object]] = []
        self.auto_start_updates: list[bool] = []
        self.fetch_repo_details = lambda owner, name: {"full_name": f"{owner}/{name}"}
        self.fetch_user_starred = lambda: [{"full_name": "octo/demo", "url": "https://github.com/octo/demo"}]
        self.sync_local_favorites_with_starred = lambda _repos: {"total": 1, "added": 1, "removed": 0}
        self.runtime_settings = {
            "port": 8080,
            "refresh_hours": 1,
            "result_limit": 25,
            "default_sort": "stars",
            "auto_start": False,
            "github_token": "saved-token",
            "proxy": "http://127.0.0.1:7890",
        }

        def set_repo_state(state_key: str, enabled: bool, repo: object) -> None:
            if state_key not in {"favorites", "watch_later", "read", "ignored"}:
                raise ValueError("invalid state")
            if not isinstance(repo, dict) or not repo.get("url"):
                raise ValueError("missing repo")
            self.state_updates.append((state_key, enabled, repo))

        handler = make_app_handler(
            runtime_root=str(runtime_root),
            status_path=str(runtime_root / "status.json"),
            settings=self.runtime_settings,
            settings_lock=threading.RLock(),
            sanitize_settings=self._sanitize_settings,
            load_json_file=lambda _path, default: {"refreshing": False, "fetched_at": "now"} if default == {} else default,
            fetch_repo_details=lambda owner, name: self.fetch_repo_details(owner, name),
            normalize=normalize,
            as_bool=as_bool,
            set_repo_state=set_repo_state,
            export_user_state=lambda: {"favorites": [], "repo_records": {}},
            import_user_state=lambda payload: {
                "mode": payload.get("mode", "merge"),
                "before_counts": {},
                "after_counts": {},
                "user_state": {"favorites": [], "repo_records": {}},
            },
            normalize_settings=lambda payload: dict(payload),
            merge_settings=self._merge_settings,
            save_settings=lambda settings: self.saved_settings.append(dict(settings)),
            apply_runtime_settings=lambda: None,
            update_auto_start=lambda enabled: self.auto_start_updates.append(bool(enabled)),
            clamp_int=clamp_int,
            current_port=lambda: 8080,
            start_refresh_async=lambda _source: self.refresh_started,
            open_chatgpt_target=lambda _mode, _prompt: (True, "opened"),
            open_external_url=lambda _url: True,
            clear_favorite_updates=lambda: None,
            start_discovery_job=lambda _payload: {"id": "job-1", "status": "queued"},
            get_discovery_job=lambda job_id: {"id": job_id, "status": "completed"} if job_id != "missing" else (_ for _ in ()).throw(ValueError("missing")),
            cancel_discovery_job=lambda job_id: {"id": job_id, "status": "cancelled"},
            clear_discovery_results=lambda: {"last_results": []},
            export_discovery_state=lambda: {"remembered_query": {}, "last_results": []},
            export_active_discovery_job=lambda: {"id": "job-active", "status": "running"},
            open_main_window=lambda: True,
            exit_app=self._exit_app,
            sync_favorite_repo=lambda _repo, _enabled: None,
            fetch_user_starred=lambda: self.fetch_user_starred(),
            sync_local_favorites_with_starred=lambda repos: self.sync_local_favorites_with_starred(repos),
            validate_github_token=self._validate_github_token,
            control_token_getter=lambda: self.control_token,
        )
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_port

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=1)
        self.tempdir.cleanup()

    def _exit_app(self):
        self.exit_requested = True

    def _sanitize_settings(self, include_sensitive: bool = False):
        payload = {
            "port": self.runtime_settings["port"],
            "effective_port": 8080,
            "restart_required": False,
            "refresh_hours": self.runtime_settings["refresh_hours"],
            "result_limit": self.runtime_settings["result_limit"],
            "default_sort": self.runtime_settings["default_sort"],
            "auto_start": self.runtime_settings["auto_start"],
            "has_github_token": bool(self.runtime_settings["github_token"]),
            "has_proxy": bool(self.runtime_settings["proxy"]),
            "effective_proxy": "http://127.0.0.1:7890",
            "proxy_source": "configured",
            "runtime_root": str(self.runtime_root),
        }
        if include_sensitive:
            payload["github_token"] = ""
            payload["proxy"] = ""
        return payload

    def _merge_settings(self, payload: object, current: object | None = None):
        raw = payload if isinstance(payload, dict) else {}
        existing = dict(current if isinstance(current, dict) else self.runtime_settings)
        merged = dict(existing)
        merged["port"] = clamp_int(raw.get("port"), existing["port"], 1, 65535)
        merged["refresh_hours"] = clamp_int(raw.get("refresh_hours"), existing["refresh_hours"], 1, 24)
        merged["result_limit"] = clamp_int(raw.get("result_limit"), existing["result_limit"], 10, 100)
        merged["default_sort"] = normalize(raw.get("default_sort", existing["default_sort"])) or existing["default_sort"]
        merged["auto_start"] = as_bool(raw.get("auto_start"), existing["auto_start"])
        if as_bool(raw.get("clear_github_token"), False):
            merged["github_token"] = ""
        elif "github_token" in raw and normalize(raw.get("github_token", "")):
            merged["github_token"] = normalize(raw.get("github_token", ""))
        if as_bool(raw.get("clear_proxy"), False):
            merged["proxy"] = ""
        elif "proxy" in raw and normalize(raw.get("proxy", "")):
            merged["proxy"] = normalize(raw.get("proxy", ""))
        return merged

    def _validate_github_token(self, token: object | None = None):
        self.validated_tokens.append(token)
        return {"state": "success" if token is None or normalize(token) else "empty"}

    def request(
        self,
        method: str,
        path: str,
        body: dict[str, object] | None = None,
        *,
        include_token: bool = True,
        token: str | None = None,
    ):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        payload = None if body is None else json.dumps(body).encode("utf-8")
        headers: dict[str, str] = {"Content-Type": "application/json"} if payload is not None else {}
        if include_token:
            headers["X-GitSonar-Control"] = self.control_token if token is None else token
        conn.request(method, path, body=payload, headers=headers)
        resp = conn.getresponse()
        data = resp.read()
        conn.close()
        return resp, data

    def request_raw(
        self,
        method: str,
        path: str,
        body: bytes | str | None = None,
        *,
        include_token: bool = True,
        headers: dict[str, str] | None = None,
    ):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        payload = body.encode("utf-8") if isinstance(body, str) else body
        request_headers = dict(headers or {})
        if include_token:
            request_headers["X-GitSonar-Control"] = self.control_token
        conn.request(method, path, body=payload, headers=request_headers)
        resp = conn.getresponse()
        data = resp.read()
        conn.close()
        return resp, data

    def test_control_token_missing_is_rejected(self):
        resp, data = self.request("POST", "/api/refresh", include_token=False)
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 403)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["code"], "invalid_control_token")
        self.assertIn("control token", payload["error"].lower())

    def test_control_token_wrong_is_rejected(self):
        resp, data = self.request("POST", "/api/refresh", token="wrong-token")
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 403)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["code"], "invalid_control_token")
        self.assertIn("control token", payload["error"].lower())

    def test_get_status_remains_available_without_control_token(self):
        resp, data = self.request("GET", "/api/status", include_token=False)
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 200)
        self.assertFalse(payload["refreshing"])
        self.assertEqual(payload["fetched_at"], "now")

    def test_get_settings_hides_sensitive_values(self):
        resp, data = self.request("GET", "/api/settings")
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 200)
        self.assertTrue(payload["has_github_token"])
        self.assertTrue(payload["has_proxy"])
        self.assertEqual(payload["github_token"], "")
        self.assertEqual(payload["proxy"], "")
        self.assertEqual(payload["runtime_root"], str(self.runtime_root))

    def test_post_settings_blank_sensitive_values_preserve_existing_values(self):
        resp, data = self.request(
            "POST",
            "/api/settings",
            {
                "github_token": "",
                "proxy": "",
                "refresh_hours": 2,
                "result_limit": 40,
                "port": 8080,
                "auto_start": True,
                "default_sort": "gained",
            },
        )
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(self.runtime_settings["github_token"], "saved-token")
        self.assertEqual(self.runtime_settings["proxy"], "http://127.0.0.1:7890")
        self.assertEqual(self.runtime_settings["result_limit"], 40)
        self.assertEqual(self.saved_settings[-1]["github_token"], "saved-token")
        self.assertEqual(self.saved_settings[-1]["proxy"], "http://127.0.0.1:7890")
        self.assertEqual(payload["settings"]["github_token"], "")
        self.assertEqual(payload["settings"]["proxy"], "")

    def test_post_settings_clear_flags_remove_sensitive_values(self):
        resp, data = self.request(
            "POST",
            "/api/settings",
            {
                "github_token": "",
                "clear_github_token": True,
                "proxy": "",
                "clear_proxy": True,
                "refresh_hours": 1,
                "result_limit": 25,
                "port": 8080,
                "auto_start": False,
                "default_sort": "stars",
            },
        )
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(self.runtime_settings["github_token"], "")
        self.assertEqual(self.runtime_settings["proxy"], "")
        self.assertEqual(self.saved_settings[-1]["github_token"], "")
        self.assertEqual(self.saved_settings[-1]["proxy"], "")

    def test_post_token_status_without_token_uses_saved_value(self):
        resp, data = self.request("POST", "/api/settings/token-status", {})
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(self.validated_tokens[-1], None)

    def test_get_discovery_returns_state_and_active_job(self):
        resp, data = self.request("GET", "/api/discovery")
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["active_job"]["id"], "job-active")
        self.assertIn("remembered_query", payload["discovery_state"])

    def test_get_export_returns_attachment(self):
        resp, data = self.request("GET", "/api/export")

        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.getheader("Content-Disposition"), 'attachment; filename="gitsonar_backup.json"')
        self.assertIn(b'"favorites": []', data)

    def test_get_discovery_job_returns_404_for_missing_job(self):
        resp, data = self.request("GET", "/api/discovery/job?id=missing")
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 404)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["code"], "not_found")
        self.assertIn("missing", payload["error"])

    def test_post_state_updates_user_state(self):
        resp, data = self.request(
            "POST",
            "/api/state",
            {
                "state": "favorites",
                "enabled": True,
                "repo": {"full_name": "octo/demo", "url": "https://github.com/octo/demo"},
            },
        )
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(len(self.state_updates), 1)
        self.assertEqual(self.state_updates[0][0], "favorites")

    def test_post_state_returns_400_for_invalid_repo(self):
        resp, data = self.request("POST", "/api/state", {"state": "favorites", "enabled": True})
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 400)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["code"], "invalid_request")
        self.assertIn("repo", payload["error"])

    def test_post_refresh_returns_409_when_refresh_in_progress(self):
        self.refresh_started = False
        resp, data = self.request("POST", "/api/refresh")
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 409)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["code"], "refresh_in_progress")
        self.assertIn("Refresh already in progress.", payload["error"])

    def test_post_settings_replaces_sensitive_values_without_echoing_plaintext(self):
        resp, data = self.request(
            "POST",
            "/api/settings",
            {
                "github_token": "new-token",
                "proxy": "http://127.0.0.1:7999",
                "refresh_hours": 2,
                "result_limit": 30,
                "port": 8080,
                "auto_start": False,
                "default_sort": "stars",
            },
        )
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(self.runtime_settings["github_token"], "new-token")
        self.assertEqual(self.runtime_settings["proxy"], "http://127.0.0.1:7999")
        self.assertEqual(payload["settings"]["github_token"], "")
        self.assertEqual(payload["settings"]["proxy"], "")
        self.assertNotIn("new-token", data.decode("utf-8"))
        self.assertNotIn("7999", payload["settings"]["proxy"])

    def test_invalid_json_body_returns_stable_error_code(self):
        resp, data = self.request_raw(
            "POST",
            "/api/settings/token-status",
            "{",
            headers={"Content-Type": "application/json"},
        )
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 400)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["code"], "invalid_json_body")
        self.assertIn("valid JSON", payload["error"])

    def test_sync_stars_unexpected_failure_is_sanitized(self):
        self.fetch_user_starred = lambda: (_ for _ in ()).throw(RuntimeError("secret backend detail"))

        resp, data = self.request("POST", "/api/sync-stars")
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 400)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["code"], "github_star_sync_failed")
        self.assertNotIn("secret backend detail", payload["error"])

    def test_repo_details_internal_value_error_is_sanitized(self):
        self.fetch_repo_details = lambda _owner, _name: (_ for _ in ()).throw(ValueError("secret backend detail"))

        resp, data = self.request("GET", "/api/repo-details?owner=octo&name=demo")
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 500)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["code"], "repo_details_failed")
        self.assertNotIn("secret backend detail", payload["error"])

    def test_make_app_handler_preserves_legacy_signature_without_optional_control_args(self):
        handler = make_app_handler(
            runtime_root=str(self.runtime_root),
            status_path=str(self.runtime_root / "status.json"),
            settings=self.runtime_settings,
            settings_lock=threading.RLock(),
            sanitize_settings=self._sanitize_settings,
            load_json_file=lambda _path, default: {"refreshing": False, "fetched_at": "now"} if default == {} else default,
            fetch_repo_details=lambda owner, name: {"full_name": f"{owner}/{name}"},
            normalize=normalize,
            as_bool=as_bool,
            set_repo_state=lambda *_args, **_kwargs: None,
            export_user_state=lambda: {"favorites": [], "repo_records": {}},
            import_user_state=lambda payload: {"mode": payload.get("mode", "merge")},
            normalize_settings=lambda payload: dict(payload),
            save_settings=lambda _settings: None,
            apply_runtime_settings=lambda: None,
            update_auto_start=lambda _enabled: None,
            clamp_int=clamp_int,
            current_port=lambda: 8080,
            start_refresh_async=lambda _source: True,
            open_chatgpt_target=lambda _mode, _prompt: (True, "opened"),
            open_external_url=lambda _url: True,
            clear_favorite_updates=lambda: None,
            start_discovery_job=lambda _payload: {"id": "job-1", "status": "queued"},
            get_discovery_job=lambda job_id: {"id": job_id, "status": "completed"},
            cancel_discovery_job=lambda job_id: {"id": job_id, "status": "cancelled"},
            clear_discovery_results=lambda: {"last_results": []},
            export_discovery_state=lambda: {"remembered_query": {}, "last_results": []},
            export_active_discovery_job=lambda: {"id": "job-active", "status": "running"},
            open_main_window=lambda: True,
            exit_app=lambda: None,
            sync_favorite_repo=lambda _repo, _enabled: None,
            fetch_user_starred=lambda: [],
            sync_local_favorites_with_starred=lambda _repos: {"total": 0, "added": 0, "removed": 0},
            validate_github_token=lambda _token=None: {"state": "success"},
        )

        self.assertTrue(callable(handler))

    def test_removed_saved_discovery_routes_return_404(self):
        for path in ("/api/discovery/run-saved", "/api/discovery/delete"):
            with self.subTest(path=path):
                resp, _data = self.request("POST", path, {"id": "legacy"})
                self.assertEqual(resp.status, 404)

    def test_unknown_endpoint_returns_not_found_code(self):
        resp, data = self.request("POST", "/api/unknown", {"id": "missing"})
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 404)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["code"], "not_found")


if __name__ == "__main__":
    unittest.main()
