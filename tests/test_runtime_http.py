from __future__ import annotations

import http.client
import json
import sys
import tempfile
import threading
import unittest
from datetime import date
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import gitsonar.runtime.http as runtime_http
from gitsonar.runtime.http import localize_user_message, make_app_handler
from gitsonar.runtime.utils import as_bool, clamp_int, normalize


class RuntimeHTTPHandlerTests(unittest.TestCase):
    def test_localize_user_message_falls_back_for_internal_ascii_token(self):
        self.assertEqual(localize_user_message(normalize, "missing", "请求处理失败。"), "请求处理失败。")

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        runtime_root = Path(self.tempdir.name)
        self.runtime_root = runtime_root
        (runtime_root / "trending.html").write_text("<html>ok</html>", encoding="utf-8")
        self.control_token = "runtime-control-token"
        self.user_state = {
            "favorites": [],
            "watch_later": [],
            "read": [],
            "ignored": [],
            "repo_records": {},
            "repo_annotations": {},
            "favorite_watch": {},
            "favorite_updates": [],
            "feedback_signals": {},
            "ai_insights": {},
        }
        self.discovery_state = {"remembered_query": {}, "last_results": [], "saved_views": []}
        self.state_updates: list[tuple[str, bool, dict[str, object] | None]] = []
        self.batch_state_calls: list[tuple[str, bool, list[dict[str, object]]]] = []
        self.discovery_job_payloads: list[dict[str, object]] = []
        self.exit_requested = False
        self.refresh_started = True
        self.validated_tokens: list[object | None] = []
        self.saved_settings: list[dict[str, object]] = []
        self.auto_start_updates: list[bool] = []
        self.diagnostics_runs = 0
        self.status_payload = {"refreshing": False, "fetched_at": "now"}
        self.fetch_repo_details = lambda owner, name: {"full_name": f"{owner}/{name}"}
        self.fetch_user_starred = lambda: [{"full_name": "octo/demo", "url": "https://github.com/octo/demo"}]
        self.sync_local_favorites_with_starred = lambda _repos: {"total": 1, "added": 1, "removed": 0}
        self.sync_favorite_repo = lambda _repo, _enabled: None
        self.runtime_settings = {
            "port": 8080,
            "refresh_hours": 1,
            "result_limit": 25,
            "default_sort": "stars",
            "auto_start": False,
            "github_token": "saved-token",
            "proxy": "http://127.0.0.1:7890",
        }

        def apply_state_update(state_key: str, enabled: bool, repo: object) -> dict[str, object]:
            if state_key not in {"favorites", "watch_later", "read", "ignored"}:
                raise ValueError("invalid state")
            if not isinstance(repo, dict) or not repo.get("url"):
                raise ValueError("missing repo")
            clean = dict(repo)
            url = str(clean["url"])
            self.user_state["repo_records"][url] = clean
            self.user_state[state_key] = [item for item in self.user_state.get(state_key, []) if item != url]
            if enabled:
                self.user_state[state_key].insert(0, url)
            return clean

        def set_repo_state(state_key: str, enabled: bool, repo: object) -> None:
            clean = apply_state_update(state_key, enabled, repo)
            self.state_updates.append((state_key, enabled, clean))

        def set_repo_state_batch(state_key: str, enabled: bool, repos: object) -> list[dict[str, object]]:
            if not isinstance(repos, list):
                raise ValueError("missing repos")
            processed = [apply_state_update(state_key, enabled, repo) for repo in repos]
            self.batch_state_calls.append((state_key, enabled, processed))
            return processed

        def set_repo_annotation(url: object, payload: object, repo: object | None = None):
            clean_url = normalize(url)
            if not clean_url:
                raise ValueError("missing repo")
            if isinstance(repo, dict) and repo.get("url"):
                self.user_state["repo_records"][str(repo["url"])] = dict(repo)
            raw = payload if isinstance(payload, dict) else {}
            tags = list(dict.fromkeys(normalize(item) for item in raw.get("tags", []) if normalize(item)))
            note = normalize(raw.get("note"))
            if not tags and not note:
                self.user_state["repo_annotations"].pop(clean_url, None)
                return None
            annotation = {"tags": tags[:12], "note": note, "updated_at": "now"}
            self.user_state["repo_annotations"][clean_url] = annotation
            return annotation

        def set_favorite_update_state(
            update_id: object,
            *,
            read: object | None = None,
            dismissed: object | None = None,
            pinned: object | None = None,
        ):
            clean_id = normalize(update_id)
            for index, item in enumerate(self.user_state["favorite_updates"]):
                if item.get("id") != clean_id:
                    continue
                update = dict(item)
                if read is not None:
                    update["read_at"] = "now" if bool(read) else ""
                if dismissed is not None:
                    update["dismissed_at"] = "now" if bool(dismissed) else ""
                if pinned is not None:
                    update["pinned"] = bool(pinned)
                self.user_state["favorite_updates"][index] = update
                return update
            raise ValueError("favorite update not found")

        def set_ai_insight(url: object, payload: object, repo: object | None = None):
            clean_url = normalize(url)
            if not clean_url:
                raise ValueError("missing repo")
            if not isinstance(payload, dict) or not normalize(payload.get("summary")):
                raise ValueError("invalid ai insight")
            if isinstance(repo, dict) and repo.get("url"):
                self.user_state["repo_records"][str(repo["url"])] = dict(repo)
            insight = dict(payload)
            insight.setdefault("schema_version", "gitsonar.repo_insight.v1")
            insight.setdefault("provider", "manual")
            self.user_state["ai_insights"][clean_url] = insight
            return insight

        def delete_ai_insight(url: object):
            clean_url = normalize(url)
            if not clean_url:
                raise ValueError("missing repo")
            self.user_state["ai_insights"].pop(clean_url, None)
            return json.loads(json.dumps(self.user_state))

        def save_discovery_view(payload: object):
            raw = dict(payload) if isinstance(payload, dict) else {}
            if not normalize(raw.get("id")) or not normalize(raw.get("name")) or not normalize(raw.get("query")):
                raise ValueError("missing discovery view")
            view = {
                "id": normalize(raw.get("id")),
                "name": normalize(raw.get("name")),
                "query": normalize(raw.get("query")),
                "limit": clamp_int(raw.get("limit"), 25, 5, 100),
                "auto_expand": as_bool(raw.get("auto_expand"), True),
                "ranking_profile": normalize(raw.get("ranking_profile")) or "balanced",
                "last_run_at": normalize(raw.get("last_run_at")),
                "last_result_count": clamp_int(raw.get("last_result_count"), 0, 0, 999),
            }
            remaining = [item for item in self.discovery_state["saved_views"] if item.get("id") != view["id"]]
            self.discovery_state["saved_views"] = [view, *remaining][:20]
            return view

        def delete_discovery_view(view_id: object):
            clean_id = normalize(view_id)
            before = len(self.discovery_state["saved_views"])
            self.discovery_state["saved_views"] = [
                item for item in self.discovery_state["saved_views"] if item.get("id") != clean_id
            ]
            if len(self.discovery_state["saved_views"]) == before:
                raise ValueError("discovery view not found")
            return json.loads(json.dumps(self.discovery_state))

        def run_diagnostics():
            self.diagnostics_runs += 1
            return {
                "generated_at": "now",
                "items": [
                    {"key": "github_api", "title": "GitHub API", "state": "ok", "summary": "reachable"},
                    {"key": "proxy", "title": "代理配置", "state": "warn", "summary": "not set"},
                ],
                "has_errors": False,
            }


        def start_discovery_job(payload: object) -> dict[str, object]:
            clean = dict(payload) if isinstance(payload, dict) else {}
            self.discovery_job_payloads.append(clean)
            return {"id": "job-1", "status": "queued"}

        def export_api_repos(**kwargs):
            return {
                "ok": True,
                "view": kwargs.get("view") or "all",
                "state": kwargs.get("state") or "",
                "q": kwargs.get("q") or "",
                "count": 1,
                "repos": [
                    {
                        "full_name": "octo/demo",
                        "url": "https://github.com/octo/demo",
                        "description": "Demo repo",
                    }
                ],
            }

        handler = make_app_handler(
            runtime_root=str(runtime_root),
            status_path=str(runtime_root / "status.json"),
            settings=self.runtime_settings,
            settings_lock=threading.RLock(),
            sanitize_settings=self._sanitize_settings,
            load_json_file=lambda _path, default: dict(self.status_payload) if default == {} else default,
            fetch_repo_details=lambda owner, name: self.fetch_repo_details(owner, name),
            normalize=normalize,
            as_bool=as_bool,
            set_repo_state=set_repo_state,
            set_repo_state_batch=set_repo_state_batch,
            set_repo_annotation=set_repo_annotation,
            set_favorite_update_state=set_favorite_update_state,
            export_user_state=lambda: json.loads(json.dumps(self.user_state)),
            set_ai_insight=set_ai_insight,
            delete_ai_insight=delete_ai_insight,
            import_user_state=lambda payload: {
                "mode": payload.get("mode", "merge"),
                "before_counts": {},
                "after_counts": {},
                "user_state": json.loads(json.dumps(self.user_state)),
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
            start_discovery_job=start_discovery_job,
            get_discovery_job=lambda job_id: {"id": job_id, "status": "completed"} if job_id != "missing" else (_ for _ in ()).throw(ValueError("missing")),
            cancel_discovery_job=lambda job_id: {"id": job_id, "status": "cancelled"},
            save_discovery_view=save_discovery_view,
            delete_discovery_view=delete_discovery_view,
            clear_discovery_results=lambda: {"last_results": []},
            export_discovery_state=lambda: json.loads(json.dumps(self.discovery_state)),
            export_active_discovery_job=lambda: {"id": "job-active", "status": "running"},
            open_main_window=lambda: True,
            exit_app=self._exit_app,
            sync_favorite_repo=lambda repo, enabled: self.sync_favorite_repo(repo, enabled),
            fetch_user_starred=lambda: self.fetch_user_starred(),
            sync_local_favorites_with_starred=lambda repos: self.sync_local_favorites_with_starred(repos),
            validate_github_token=self._validate_github_token,
            run_diagnostics=run_diagnostics,
            export_api_bootstrap=lambda: {
                "ok": True,
                "settings": self._sanitize_settings(False),
                "counts": {"repos": 1, "favorite_updates": 0},
            },
            export_api_repos=export_api_repos,
            export_api_updates=lambda: {"ok": True, "count": 0, "updates": []},
            export_api_discovery_views=lambda: {"ok": True, "count": 0, "views": []},
            export_ai_artifacts=lambda: {
                "ok": True,
                "count": 1,
                "artifacts": [
                    {
                        "url": "https://github.com/octo/demo",
                        "artifact_id": "repo_insight_demo",
                        "artifact_type": "repo_insight",
                    }
                ],
            },
            export_jobs=lambda **kwargs: {
                "ok": True,
                "status": kwargs.get("status") or "",
                "count": 1,
                "jobs": [{"id": "job-1", "job_type": "refresh", "status": "running"}],
            },
            export_events=lambda **kwargs: {
                "ok": True,
                "after_id": kwargs.get("after_id") or "",
                "count": 1,
                "events": [{"id": "event-1", "event_type": "job.updated", "job_id": "job-1"}],
            },
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
            "runtime_root": "",
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
        self.assertIn("控制令牌", payload["error"])

    def test_control_token_wrong_is_rejected(self):
        resp, data = self.request("POST", "/api/refresh", token="wrong-token")
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 403)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["code"], "invalid_control_token")
        self.assertIn("控制令牌", payload["error"])

    def test_get_status_remains_available_without_control_token(self):
        resp, data = self.request("GET", "/api/status", include_token=False)
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 200)
        self.assertFalse(payload["refreshing"])
        self.assertEqual(payload["fetched_at"], "now")

    def test_get_status_redacts_legacy_sensitive_error(self):
        self.status_payload = {
            "refreshing": False,
            "fetched_at": "old",
            "error": "ghp_secret_token http://user:pass@127.0.0.1:7890 C:\\Users\\liushun\\runtime-data",
        }

        resp, data = self.request("GET", "/api/status", include_token=False)
        payload = json.loads(data.decode("utf-8"))
        payload_text = data.decode("utf-8")

        self.assertEqual(resp.status, 200)
        self.assertTrue(payload["error"])
        self.assertNotIn("ghp_secret_token", payload_text)
        self.assertNotIn("user:pass", payload_text)
        self.assertNotIn("C:\\Users\\liushun", payload_text)

    def test_get_settings_hides_sensitive_values(self):
        resp, data = self.request("GET", "/api/settings")
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 200)
        self.assertTrue(payload["has_github_token"])
        self.assertTrue(payload["has_proxy"])
        self.assertEqual(payload["github_token"], "")
        self.assertEqual(payload["proxy"], "")
        self.assertEqual(payload["runtime_root"], "")

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

    def test_get_bootstrap_repos_updates_and_discovery_views(self):
        resp, data = self.request("GET", "/api/bootstrap")
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["counts"]["repos"], 1)
        self.assertTrue(payload["settings"]["has_github_token"])
        self.assertNotIn("saved-token", data.decode("utf-8"))

        resp, data = self.request("GET", "/api/repos?view=daily&q=demo")
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["view"], "daily")
        self.assertEqual(payload["q"], "demo")
        self.assertEqual(payload["repos"][0]["full_name"], "octo/demo")

        resp, data = self.request("GET", "/api/updates")
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["updates"], [])

        resp, data = self.request("GET", "/api/discovery/views")
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["views"], [])

    def test_get_jobs_and_events_return_runtime_event_payloads(self):
        resp, data = self.request("GET", "/api/jobs?status=running")
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["status"], "running")
        self.assertEqual(payload["jobs"][0]["id"], "job-1")

        resp, data = self.request("GET", "/api/events?after_id=event-0")
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["after_id"], "event-0")
        self.assertEqual(payload["events"][0]["event_type"], "job.updated")

    def test_get_ai_artifacts_returns_local_artifact_list(self):
        resp, data = self.request("GET", "/api/ai-artifacts")
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["artifacts"][0]["artifact_type"], "repo_insight")

    def test_get_events_stream_returns_sse_snapshot_and_requires_control_token(self):
        resp, data = self.request("GET", "/api/events/stream?after_id=event-0")
        body = data.decode("utf-8")

        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.getheader("Content-Type"), "text/event-stream; charset=utf-8")
        self.assertIn("id: event-1", body)
        self.assertIn("event: job.updated", body)
        self.assertIn('"job_id": "job-1"', body)

        resp, data = self.request("GET", "/api/events/stream", include_token=False)
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 403)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["code"], "invalid_control_token")

    def test_get_diagnostics_returns_local_runtime_report(self):
        resp, data = self.request("GET", "/api/diagnostics")
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["diagnostics"]["generated_at"], "now")
        self.assertEqual(self.diagnostics_runs, 1)
        self.assertEqual(payload["diagnostics"]["items"][0]["key"], "github_api")

    def test_get_export_returns_attachment(self):
        resp, data = self.request("GET", "/api/export")

        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.getheader("Content-Disposition"), 'attachment; filename="gitsonar_backup.json"')
        self.assertIn(b'"favorites": []', data)

    def test_post_analysis_export_markdown_returns_attachment(self):
        markdown = "# GitSonar 分析导出\n\n完整内容\n"
        resp, data = self.request(
            "POST",
            "/api/analysis/export-markdown",
            {
                "filename": "gitsonar-analysis-visible-2026-04-20.md",
                "content": markdown,
            },
        )

        self.assertEqual(resp.status, 200)
        self.assertEqual(
            resp.getheader("Content-Disposition"),
            'attachment; filename="gitsonar-analysis-visible-2026-04-20.md"',
        )
        self.assertEqual(resp.getheader("Content-Type"), "text/markdown; charset=utf-8")
        self.assertEqual(data.decode("utf-8"), markdown)

    def test_post_analysis_export_markdown_rejects_missing_or_empty_content(self):
        for body in (
            {"filename": "gitsonar-analysis-visible-2026-04-20.md"},
            {"filename": "gitsonar-analysis-visible-2026-04-20.md", "content": ""},
        ):
            with self.subTest(body=body):
                resp, data = self.request("POST", "/api/analysis/export-markdown", body)
                payload = json.loads(data.decode("utf-8"))

                self.assertEqual(resp.status, 400)
                self.assertFalse(payload["ok"])
                self.assertEqual(payload["code"], "analysis_export_invalid")
                self.assertIn("Markdown", payload["error"])

    def test_post_analysis_export_markdown_falls_back_for_invalid_filename(self):
        markdown = "# GitSonar 分析导出\n"
        resp, data = self.request(
            "POST",
            "/api/analysis/export-markdown",
            {
                "filename": "../unsafe name.md",
                "content": markdown,
            },
        )

        self.assertEqual(resp.status, 200)
        self.assertEqual(
            resp.getheader("Content-Disposition"),
            f'attachment; filename="gitsonar-analysis-{date.today().isoformat()}.md"',
        )
        self.assertEqual(data.decode("utf-8"), markdown)

    def test_get_discovery_job_returns_404_for_missing_job(self):
        resp, data = self.request("GET", "/api/discovery/job?id=missing")
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 404)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["code"], "not_found")
        self.assertIn("关键词发现任务", payload["error"])

    def test_post_discover_passes_limit_and_ranking_profile_to_job_service(self):
        resp, data = self.request(
            "POST",
            "/api/discover",
            {"query": "agent", "limit": 100, "auto_expand": True, "ranking_profile": "hot"},
        )
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(self.discovery_job_payloads[-1]["limit"], 100)
        self.assertEqual(self.discovery_job_payloads[-1]["ranking_profile"], "hot")

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
        self.assertIn("仓库信息", payload["error"])

    def test_post_state_ignored_includes_feedback_reason(self):
        resp, data = self.request(
            "POST",
            "/api/state",
            {
                "state": "ignored",
                "enabled": True,
                "feedback_reason": "只是 demo",
                "repo": {"full_name": "octo/demo", "url": "https://github.com/octo/demo"},
            },
        )
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(self.state_updates[-1][0], "ignored")
        self.assertEqual(self.state_updates[-1][2]["feedback_reason"], "只是 demo")

    def test_post_repo_annotations_persists_tags_and_note(self):
        resp, data = self.request(
            "POST",
            "/api/repo-annotations",
            {
                "url": "https://github.com/octo/demo",
                "repo": {"full_name": "octo/demo", "url": "https://github.com/octo/demo"},
                "tags": ["agent", "tooling", "agent"],
                "note": "  值得后续复看  ",
            },
        )
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["annotation"]["tags"], ["agent", "tooling"])
        self.assertEqual(payload["annotation"]["note"], "值得后续复看")
        self.assertIn("https://github.com/octo/demo", payload["user_state"]["repo_annotations"])

    def test_post_favorite_update_state_marks_read_dismissed_and_pinned(self):
        self.user_state["favorite_updates"] = [
            {
                "id": "update-1",
                "full_name": "octo/demo",
                "url": "https://github.com/octo/demo",
                "checked_at": "2026-04-23T00:00:00",
                "changes": ["release"],
                "read_at": "",
                "dismissed_at": "",
                "pinned": False,
            }
        ]

        resp, data = self.request(
            "POST",
            "/api/favorite-updates/state",
            {"id": "update-1", "read": True, "dismissed": True, "pinned": True},
        )
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["update"]["read_at"], "now")
        self.assertEqual(payload["update"]["dismissed_at"], "now")
        self.assertTrue(payload["update"]["pinned"])

    def test_post_state_batch_updates_user_state_with_single_local_commit(self):
        repos = [
            {"full_name": "octo/one", "url": "https://github.com/octo/one"},
            {"full_name": "octo/two", "url": "https://github.com/octo/two"},
        ]

        resp, data = self.request(
            "POST",
            "/api/state/batch",
            {"state": "watch_later", "enabled": True, "repos": repos},
        )
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["processed_count"], 2)
        self.assertEqual(self.state_updates, [])
        self.assertEqual(len(self.batch_state_calls), 1)
        self.assertEqual(payload["user_state"]["watch_later"], ["https://github.com/octo/two", "https://github.com/octo/one"])

    def test_post_state_batch_returns_partial_success_when_github_star_sync_fails_midway(self):
        repos = [
            {"full_name": "octo/one", "url": "https://github.com/octo/one"},
            {"full_name": "octo/two", "url": "https://github.com/octo/two"},
            {"full_name": "octo/three", "url": "https://github.com/octo/three"},
        ]
        sync_calls: list[str] = []

        def sync_favorite_repo(repo: object, _enabled: bool):
            full_name = str((repo or {}).get("full_name") or "")
            sync_calls.append(full_name)
            if full_name == "octo/two":
                return {"ok": False, "error": "remote failed"}
            return {"ok": True, "message": f"synced {full_name}"}

        self.sync_favorite_repo = sync_favorite_repo

        resp, data = self.request(
            "POST",
            "/api/state/batch",
            {"state": "favorites", "enabled": True, "repos": repos},
        )
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 400)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["processed_count"], 1)
        self.assertEqual(sync_calls, ["octo/one", "octo/two"])
        self.assertEqual(len(self.batch_state_calls), 1)
        self.assertEqual(payload["user_state"]["favorites"], ["https://github.com/octo/one"])
        self.assertEqual(len(payload["github_star_syncs"]), 1)
        self.assertEqual(payload["github_star_syncs"][0]["full_name"], "octo/one")

    def test_post_state_batch_syncs_favorites_in_input_order(self):
        repos = [
            {"full_name": "octo/one", "url": "https://github.com/octo/one"},
            {"full_name": "octo/two", "url": "https://github.com/octo/two"},
            {"full_name": "octo/three", "url": "https://github.com/octo/three"},
        ]
        sync_calls: list[str] = []

        def sync_favorite_repo(repo: object, _enabled: bool):
            full_name = str((repo or {}).get("full_name") or "")
            sync_calls.append(full_name)
            return {"ok": True, "message": full_name}

        self.sync_favorite_repo = sync_favorite_repo

        resp, data = self.request(
            "POST",
            "/api/state/batch",
            {"state": "favorites", "enabled": True, "repos": repos},
        )
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(sync_calls, ["octo/one", "octo/two", "octo/three"])
        self.assertEqual(payload["processed_count"], 3)
        self.assertEqual(len(payload["github_star_syncs"]), 3)

    def test_post_discovery_view_save_and_delete_round_trip(self):
        resp, data = self.request(
            "POST",
            "/api/discovery/views",
            {
                "id": "view-1",
                "name": "Agent Builder",
                "query": "agent",
                "limit": 25,
                "auto_expand": True,
                "ranking_profile": "builder",
                "last_result_count": 12,
            },
        )
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["view"]["id"], "view-1")
        self.assertEqual(payload["discovery_state"]["saved_views"][0]["name"], "Agent Builder")

        resp, data = self.request("POST", "/api/discovery/views/delete", {"id": "view-1"})
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["discovery_state"]["saved_views"], [])

    def test_post_ai_insight_save_and_delete_round_trip(self):
        resp, data = self.request(
            "POST",
            "/api/ai-insights",
            {
                "url": "https://github.com/octo/demo",
                "repo": {"full_name": "octo/demo", "url": "https://github.com/octo/demo"},
                "insight": {
                    "summary": "适合学习仓库组织方式",
                    "best_for": ["学习结构"],
                    "next_actions": ["先读 README"],
                },
            },
        )
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["insight"]["schema_version"], "gitsonar.repo_insight.v1")
        self.assertEqual(payload["user_state"]["ai_insights"]["https://github.com/octo/demo"]["summary"], "适合学习仓库组织方式")

        resp, data = self.request("POST", "/api/ai-insights/delete", {"url": "https://github.com/octo/demo"})
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["user_state"]["ai_insights"], {})

    def test_post_refresh_returns_409_when_refresh_in_progress(self):
        self.refresh_started = False
        resp, data = self.request("POST", "/api/refresh")
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 409)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["code"], "refresh_in_progress")
        self.assertIn("后台刷新已在进行中", payload["error"])

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
        self.assertIn("合法的 JSON", payload["error"])

    def test_oversized_json_body_returns_payload_too_large(self):
        body = json.dumps({"github_token": "x" * 128}).encode("utf-8")

        with patch.object(runtime_http, "MAX_JSON_BODY_BYTES", 32, create=True):
            resp, data = self.request_raw(
                "POST",
                "/api/settings/token-status",
                body,
                headers={"Content-Type": "application/json"},
            )
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 413)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["code"], "payload_too_large")

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

    def test_repo_details_requires_control_token(self):
        resp, data = self.request("GET", "/api/repo-details?owner=octo&name=demo", include_token=False)
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(resp.status, 403)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["code"], "invalid_control_token")

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
