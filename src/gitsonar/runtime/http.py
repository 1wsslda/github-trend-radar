#!/usr/bin/env python3
from __future__ import annotations

"""HTTP request handler factory for the local runtime server."""

import json
import logging
from dataclasses import dataclass
from http.server import SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class JsonResult:
    body: object
    status: int = 200


@dataclass(frozen=True, slots=True)
class AttachmentResult:
    body: bytes
    filename: str
    content_type: str = "application/octet-stream"
    status: int = 200


@dataclass(frozen=True, slots=True)
class Route:
    handler: object
    loopback_only: bool = False
    control_only: bool = False
    json_body: bool = False
    error_status: int = 400
    error_code: str | None = None
    error_message: str | None = None


class LocalAPIError(Exception):
    def __init__(self, message: str, *, status: int = 400, code: str | None = None):
        super().__init__(message)
        self.status = status
        self.code = code


class InvalidJsonBodyError(LocalAPIError):
    def __init__(self, message: str = "Request body must be valid JSON."):
        super().__init__(message, status=400, code="invalid_json_body")


def make_app_handler(
    *,
    runtime_root: str,
    status_path: str,
    settings: dict[str, object],
    settings_lock,
    sanitize_settings,
    load_json_file,
    fetch_repo_details,
    normalize,
    as_bool,
    set_repo_state,
    export_user_state,
    import_user_state,
    normalize_settings,
    save_settings,
    apply_runtime_settings,
    update_auto_start,
    clamp_int,
    current_port,
    start_refresh_async,
    open_chatgpt_target,
    open_external_url,
    clear_favorite_updates,
    start_discovery_job,
    get_discovery_job,
    cancel_discovery_job,
    clear_discovery_results,
    export_discovery_state,
    export_active_discovery_job,
    open_main_window,
    exit_app,
    sync_favorite_repo,
    fetch_user_starred,
    sync_local_favorites_with_starred,
    validate_github_token,
    merge_settings=None,
    control_token_getter=None,
):
    merge_settings = merge_settings or (lambda payload, _current=None: normalize_settings(payload))
    control_token_getter = control_token_getter or (lambda: "")

    def error_payload(message: str, code: str | None = None) -> dict[str, object]:
        payload: dict[str, object] = {"ok": False, "error": message}
        if code:
            payload["code"] = code
        return payload

    def json_error(message: str, status: int, code: str | None = None) -> JsonResult:
        return JsonResult(error_payload(message, code), status)

    def exception_to_error(route: Route, path: str, exc: Exception) -> JsonResult:
        raw_message = normalize(str(exc))
        if isinstance(exc, LocalAPIError):
            status = int(getattr(exc, "status", route.error_status) or route.error_status)
            code = normalize(getattr(exc, "code", "")) or ("not_found" if status == 404 else (route.error_code or "invalid_request"))
            logger.warning("http_request_rejected path=%s code=%s error=%s", path, code, raw_message)
            return json_error(raw_message or "Request could not be processed.", status, code)
        code = route.error_code or ("internal_error" if route.error_status >= 500 else "request_failed")
        message = route.error_message or ("服务器内部错误。" if route.error_status >= 500 else "请求处理失败。")
        logger.exception("http_route_failed path=%s code=%s", path, code)
        return json_error(message, route.error_status, code)

    def parse_repo_details_query(parsed):
        params = parse_qs(parsed.query)
        return (params.get("owner") or [""])[0], (params.get("name") or [""])[0]

    def handle_get_settings(_handler, _parsed, _payload):
        return sanitize_settings(_handler.is_loopback_request())

    def handle_get_status(_handler, _parsed, _payload):
        return load_json_file(status_path, {})

    def handle_get_repo_details(_handler, parsed, _payload):
        owner, name = parse_repo_details_query(parsed)
        if not owner or not name:
            raise LocalAPIError("缺少仓库参数。")
        details = fetch_repo_details(owner, name)
        return {"ok": True, "details": details}

    def handle_get_discovery(_handler, _parsed, _payload):
        return {
            "ok": True,
            "discovery_state": export_discovery_state(),
            "active_job": export_active_discovery_job(),
        }

    def handle_get_discovery_job(_handler, parsed, _payload):
        params = parse_qs(parsed.query)
        try:
            job = get_discovery_job((params.get("id") or [""])[0])
        except ValueError as exc:
            raise LocalAPIError(normalize(str(exc)) or "未找到对应的 discovery job。", status=404, code="not_found") from exc
        return {"ok": True, "job": job}

    def handle_get_export(_handler, _parsed, _payload):
        body = json.dumps(export_user_state(), ensure_ascii=False, indent=2).encode("utf-8")
        return AttachmentResult(
            body=body,
            filename="gitsonar_backup.json",
            content_type="application/json; charset=utf-8",
        )

    def handle_post_state(_handler, _parsed, payload):
        state_key = normalize(payload.get("state"))
        enabled = as_bool(payload.get("enabled"), True)
        github_star_sync = None
        if state_key == "favorites":
            try:
                github_star_sync = sync_favorite_repo(payload.get("repo"), enabled)
            except ValueError as exc:
                raise LocalAPIError(normalize(str(exc)) or "缺少仓库信息。") from exc
            if github_star_sync and not (
                github_star_sync.get("ok")
                or github_star_sync.get("already_starred")
                or github_star_sync.get("already_unstarred")
            ):
                return JsonResult(github_star_sync, 400)
        try:
            set_repo_state(state_key, enabled, payload.get("repo"))
        except ValueError as exc:
            raise LocalAPIError(normalize(str(exc)) or "Request could not be processed.") from exc
        return {
            "ok": True,
            "user_state": export_user_state(),
            "github_star_sync": github_star_sync,
        }

    def handle_post_import(_handler, _parsed, payload):
        try:
            result = import_user_state(payload)
        except ValueError as exc:
            raise LocalAPIError(normalize(str(exc)) or "Import failed.") from exc
        return {"ok": True, "message": "User state imported.", **result}

    def handle_post_settings(_handler, _parsed, payload):
        try:
            requested = merge_settings(payload, settings)
        except ValueError as exc:
            raise LocalAPIError(normalize(str(exc)) or "Settings could not be saved.") from exc
        with settings_lock:
            settings.clear()
            settings.update(requested)
            save_settings(settings)
            apply_runtime_settings()
        try:
            update_auto_start(bool(settings.get("auto_start")))
        except Exception as exc:
            logger.warning("Failed to update auto-start entry after saving settings: %s", exc)
        restart_required = bool(clamp_int(settings.get("port", 8080), 8080, 1, 65535) != current_port())
        message = (
            f"Settings saved. Port will switch to {settings.get('port', 8080)} after restart."
            if restart_required
            else "Settings saved."
        )
        return {"ok": True, "message": message, "settings": sanitize_settings(True)}

    def handle_post_token_status(_handler, _parsed, payload):
        token = payload.get("github_token") if isinstance(payload, dict) and "github_token" in payload else None
        status = validate_github_token(token)
        return {"ok": True, "status": status}

    def handle_post_refresh(_handler, _parsed, _payload):
        if start_refresh_async("manual"):
            return {"ok": True, "message": "Background refresh started."}
        return json_error("Refresh already in progress.", 409, "refresh_in_progress")

    def handle_post_chatgpt_open(_handler, _parsed, payload):
        ok, message = open_chatgpt_target(payload.get("mode", "web"), payload.get("prompt", ""))
        return JsonResult({"ok": ok, "message": message}, 200 if ok else 400)

    def handle_post_open_external(_handler, _parsed, payload):
        url = normalize(payload.get("url"))
        if not url:
            raise LocalAPIError("Missing URL.")
        opened = open_external_url(url)
        return JsonResult({"ok": opened, "url": url}, 200 if opened else 500)

    def handle_post_clear_favorite_updates(_handler, _parsed, _payload):
        clear_favorite_updates()
        return {
            "ok": True,
            "message": "Favorite updates cleared.",
            "user_state": export_user_state(),
        }

    def handle_post_discover(_handler, _parsed, payload):
        try:
            job = start_discovery_job(payload)
        except ValueError as exc:
            raise LocalAPIError(normalize(str(exc)) or "Discovery job could not be started.") from exc
        return {"ok": True, "message": "Discovery job started.", "job": job}

    def handle_post_discovery_cancel(_handler, _parsed, payload):
        try:
            job = cancel_discovery_job(normalize(payload.get("id")))
        except ValueError as exc:
            raise LocalAPIError(normalize(str(exc)) or "Cancellation could not be requested.") from exc
        return {"ok": True, "message": "Cancellation requested.", "job": job}

    def handle_post_discovery_clear(_handler, _parsed, _payload):
        discovery_state = clear_discovery_results()
        return {"ok": True, "message": "Discovery results cleared.", "discovery_state": discovery_state}

    def handle_post_window_open(_handler, _parsed, _payload):
        return {"ok": True, "opened": open_main_window()}

    def handle_post_window_exit(_handler, _parsed, _payload):
        exit_app()
        return {"ok": True, "message": "Application exit requested."}

    def handle_post_sync_stars(_handler, _parsed, _payload):
        try:
            starred = fetch_user_starred()
        except ValueError as exc:
            raise LocalAPIError(normalize(str(exc)) or "请先在设置中配置 GitHub Token。", code="github_token_missing") from exc
        summary = sync_local_favorites_with_starred(starred)
        total = int(summary.get("total") or 0)
        added = int(summary.get("added") or 0)
        removed = int(summary.get("removed") or 0)
        message = f"GitHub stars synced: total {total}, added {added}, removed {removed}."
        return {
            "ok": True,
            "total": total,
            "added": added,
            "removed": removed,
            "message": message,
            "user_state": export_user_state(),
        }

    GET_ROUTES = {
        "/api/settings": Route(handle_get_settings),
        "/api/status": Route(handle_get_status),
        "/api/repo-details": Route(handle_get_repo_details, error_status=500, error_code="repo_details_failed", error_message="仓库详情加载失败。"),
        "/api/discovery": Route(handle_get_discovery),
        "/api/discovery/job": Route(handle_get_discovery_job, error_status=404, error_code="not_found"),
        "/api/export": Route(handle_get_export, loopback_only=True, control_only=True, error_status=500, error_code="export_failed", error_message="导出用户数据失败。"),
    }

    POST_ROUTES = {
        "/api/state": Route(handle_post_state, loopback_only=True, control_only=True, json_body=True),
        "/api/import": Route(handle_post_import, loopback_only=True, control_only=True, json_body=True),
        "/api/settings": Route(handle_post_settings, loopback_only=True, control_only=True, json_body=True),
        "/api/settings/token-status": Route(handle_post_token_status, loopback_only=True, control_only=True, json_body=True),
        "/api/refresh": Route(handle_post_refresh, loopback_only=True, control_only=True),
        "/api/chatgpt/open": Route(handle_post_chatgpt_open, loopback_only=True, control_only=True, json_body=True),
        "/api/open-external": Route(handle_post_open_external, loopback_only=True, control_only=True, json_body=True, error_status=500, error_code="open_external_failed", error_message="打开外部链接失败。"),
        "/api/favorite-updates/clear": Route(handle_post_clear_favorite_updates, loopback_only=True, control_only=True),
        "/api/discover": Route(handle_post_discover, loopback_only=True, control_only=True, json_body=True),
        "/api/discovery/cancel": Route(handle_post_discovery_cancel, loopback_only=True, control_only=True, json_body=True, error_code="discovery_cancel_failed"),
        "/api/discovery/clear": Route(handle_post_discovery_clear, loopback_only=True, control_only=True),
        "/api/window/open": Route(handle_post_window_open, loopback_only=True, control_only=True),
        "/api/window/exit": Route(handle_post_window_exit, loopback_only=True, control_only=True),
        "/api/sync-stars": Route(
            handle_post_sync_stars,
            loopback_only=True,
            control_only=True,
            error_status=400,
            error_code="github_star_sync_failed",
            error_message="GitHub 星标同步失败，请检查 Token 和网络后重试。",
        ),
    }

    class AppHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=runtime_root, **kwargs)

        def log_message(self, _fmt, *_args):
            pass

        def client_ip(self) -> str:
            return normalize(self.client_address[0] if self.client_address else "")

        def is_loopback_request(self) -> bool:
            return self.client_ip() in {"127.0.0.1", "::1", "::ffff:127.0.0.1"}

        def require_loopback(self) -> bool:
            if self.is_loopback_request():
                return True
            self.send_json(error_payload("This action is only available from localhost.", "loopback_only"), 403)
            return False

        def require_control_token(self) -> bool:
            expected = normalize(control_token_getter())
            if not expected:
                return True
            actual = normalize(self.headers.get("X-GitSonar-Control", ""))
            if actual == expected:
                return True
            self.send_json(error_payload("Missing or invalid control token.", "invalid_control_token"), 403)
            return False

        def end_headers(self):
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            super().end_headers()

        def send_json(self, payload: object, status: int = 200):
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def send_attachment(self, result: AttachmentResult):
            self.send_response(result.status)
            self.send_header("Content-Type", result.content_type)
            self.send_header("Content-Length", str(len(result.body)))
            self.send_header("Content-Disposition", f'attachment; filename="{result.filename}"')
            self.end_headers()
            self.wfile.write(result.body)

        def read_json(self) -> dict[str, object]:
            raw_length = self.headers.get("Content-Length", "0")
            try:
                length = max(0, int(raw_length))
            except (TypeError, ValueError):
                logger.warning("Invalid Content-Length received: %r; treating as 0", raw_length)
                length = 0
            raw_body = self.rfile.read(length).decode("utf-8") if length else "{}"
            if not raw_body.strip():
                return {}
            try:
                payload = json.loads(raw_body)
            except json.JSONDecodeError as exc:
                raise InvalidJsonBodyError() from exc
            if not isinstance(payload, dict):
                raise InvalidJsonBodyError("Request body must be a JSON object.")
            return payload

        def execute_route(self, route: Route, parsed):
            if (route.loopback_only or route.control_only) and not self.require_loopback():
                return
            if route.control_only and not self.require_control_token():
                return
            try:
                payload = self.read_json() if route.json_body else None
                result = route.handler(self, parsed, payload)
            except Exception as exc:
                error = exception_to_error(route, parsed.path, exc)
                self.send_json(error.body, error.status)
                return
            if isinstance(result, AttachmentResult):
                self.send_attachment(result)
                return
            if isinstance(result, JsonResult):
                self.send_json(result.body, result.status)
                return
            self.send_json(result)

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path in {"/", "/trending.html"}:
                self.path = "/trending.html"
                return super().do_GET()
            route = GET_ROUTES.get(parsed.path)
            if route is None:
                return self.send_json(error_payload("Unknown endpoint.", "not_found"), 404)
            return self.execute_route(route, parsed)

        def do_POST(self):
            parsed = urlparse(self.path)
            route = POST_ROUTES.get(parsed.path)
            if route is None:
                return self.send_json(error_payload("Unknown endpoint.", "not_found"), 404)
            return self.execute_route(route, parsed)

    return AppHandler
