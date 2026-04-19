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
    def __init__(self, message: str = "请求体必须是合法的 JSON。"):
        super().__init__(message, status=400, code="invalid_json_body")


LEGACY_USER_MESSAGE_MAP = {
    "Request could not be processed.": "请求处理失败。",
    "Import failed.": "导入失败。",
    "Settings could not be saved.": "保存设置失败。",
    "Refresh already in progress.": "后台刷新已在进行中。",
    "Missing URL.": "缺少链接地址。",
    "missing repo": "缺少仓库信息。",
    "missing repos": "缺少仓库列表。",
    "invalid state": "状态参数无效。",
    "Import file does not contain any restorable user state.": "导入文件中没有可恢复的用户数据。",
}


def should_use_message_fallback(message: str) -> bool:
    return bool(message) and message.isascii() and all(ch.isalnum() or ch in {"_", "-", "."} for ch in message)


def localize_user_message(normalize, message: str, fallback: str) -> str:
    clean = normalize(message)
    if not clean:
        return fallback
    mapped = LEGACY_USER_MESSAGE_MAP.get(clean)
    if mapped:
        return mapped
    if should_use_message_fallback(clean):
        return fallback
    return clean


@dataclass(frozen=True, slots=True)
class SettingsService:
    settings: dict[str, object]
    settings_lock: object
    sanitize_settings: object
    normalize_settings: object
    save_settings: object
    apply_runtime_settings: object
    update_auto_start: object
    clamp_int: object
    current_port: object
    validate_github_token: object
    merge_settings: object | None = None


@dataclass(frozen=True, slots=True)
class UserStateService:
    set_repo_state: object
    export_user_state: object
    import_user_state: object
    clear_favorite_updates: object
    sync_favorite_repo: object
    fetch_user_starred: object
    sync_local_favorites_with_starred: object
    set_repo_state_batch: object | None = None


@dataclass(frozen=True, slots=True)
class DiscoveryService:
    start_discovery_job: object
    get_discovery_job: object
    cancel_discovery_job: object
    clear_discovery_results: object
    export_discovery_state: object
    export_active_discovery_job: object


@dataclass(frozen=True, slots=True)
class ShellActions:
    open_chatgpt_target: object
    open_external_url: object
    open_main_window: object
    exit_app: object


@dataclass(frozen=True, slots=True)
class AppHandlerDeps:
    runtime_root: str
    status_path: str
    settings_service: SettingsService
    user_state_service: UserStateService
    discovery_service: DiscoveryService
    shell_actions: ShellActions
    load_json_file: object
    fetch_repo_details: object
    normalize: object
    as_bool: object
    start_refresh_async: object
    control_token_getter: object | None = None


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
    set_repo_state_batch=None,
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
    deps = AppHandlerDeps(
        runtime_root=runtime_root,
        status_path=status_path,
        settings_service=SettingsService(
            settings=settings,
            settings_lock=settings_lock,
            sanitize_settings=sanitize_settings,
            normalize_settings=normalize_settings,
            save_settings=save_settings,
            apply_runtime_settings=apply_runtime_settings,
            update_auto_start=update_auto_start,
            clamp_int=clamp_int,
            current_port=current_port,
            validate_github_token=validate_github_token,
            merge_settings=merge_settings,
        ),
        user_state_service=UserStateService(
            set_repo_state=set_repo_state,
            set_repo_state_batch=set_repo_state_batch,
            export_user_state=export_user_state,
            import_user_state=import_user_state,
            clear_favorite_updates=clear_favorite_updates,
            sync_favorite_repo=sync_favorite_repo,
            fetch_user_starred=fetch_user_starred,
            sync_local_favorites_with_starred=sync_local_favorites_with_starred,
        ),
        discovery_service=DiscoveryService(
            start_discovery_job=start_discovery_job,
            get_discovery_job=get_discovery_job,
            cancel_discovery_job=cancel_discovery_job,
            clear_discovery_results=clear_discovery_results,
            export_discovery_state=export_discovery_state,
            export_active_discovery_job=export_active_discovery_job,
        ),
        shell_actions=ShellActions(
            open_chatgpt_target=open_chatgpt_target,
            open_external_url=open_external_url,
            open_main_window=open_main_window,
            exit_app=exit_app,
        ),
        load_json_file=load_json_file,
        fetch_repo_details=fetch_repo_details,
        normalize=normalize,
        as_bool=as_bool,
        start_refresh_async=start_refresh_async,
        control_token_getter=control_token_getter,
    )
    return build_app_handler(deps)


def build_app_handler(deps: AppHandlerDeps):
    runtime_root = deps.runtime_root
    status_path = deps.status_path
    settings = deps.settings_service.settings
    settings_lock = deps.settings_service.settings_lock
    sanitize_settings = deps.settings_service.sanitize_settings
    normalize_settings = deps.settings_service.normalize_settings
    save_settings = deps.settings_service.save_settings
    apply_runtime_settings = deps.settings_service.apply_runtime_settings
    update_auto_start = deps.settings_service.update_auto_start
    clamp_int = deps.settings_service.clamp_int
    current_port = deps.settings_service.current_port
    validate_github_token = deps.settings_service.validate_github_token
    merge_settings = deps.settings_service.merge_settings or (lambda payload, _current=None: normalize_settings(payload))
    set_repo_state = deps.user_state_service.set_repo_state
    set_repo_state_batch = deps.user_state_service.set_repo_state_batch
    export_user_state = deps.user_state_service.export_user_state
    import_user_state = deps.user_state_service.import_user_state
    clear_favorite_updates = deps.user_state_service.clear_favorite_updates
    sync_favorite_repo = deps.user_state_service.sync_favorite_repo
    fetch_user_starred = deps.user_state_service.fetch_user_starred
    sync_local_favorites_with_starred = deps.user_state_service.sync_local_favorites_with_starred
    start_discovery_job = deps.discovery_service.start_discovery_job
    get_discovery_job = deps.discovery_service.get_discovery_job
    cancel_discovery_job = deps.discovery_service.cancel_discovery_job
    clear_discovery_results = deps.discovery_service.clear_discovery_results
    export_discovery_state = deps.discovery_service.export_discovery_state
    export_active_discovery_job = deps.discovery_service.export_active_discovery_job
    open_chatgpt_target = deps.shell_actions.open_chatgpt_target
    open_external_url = deps.shell_actions.open_external_url
    open_main_window = deps.shell_actions.open_main_window
    exit_app = deps.shell_actions.exit_app
    load_json_file = deps.load_json_file
    fetch_repo_details = deps.fetch_repo_details
    normalize = deps.normalize
    as_bool = deps.as_bool
    start_refresh_async = deps.start_refresh_async
    control_token_getter = deps.control_token_getter or (lambda: "")

    if set_repo_state_batch is None:
        def set_repo_state_batch(state_key: str, enabled: bool, repos: object):
            if not isinstance(repos, list):
                raise ValueError("缺少仓库列表。")
            processed = []
            for repo in repos:
                set_repo_state(state_key, enabled, repo)
                processed.append(repo)
            return processed

    def error_payload(message: str, code: str | None = None) -> dict[str, object]:
        payload: dict[str, object] = {"ok": False, "error": message}
        if code:
            payload["code"] = code
        return payload

    def github_star_sync_ok(result: object) -> bool:
        return isinstance(result, dict) and (
            result.get("ok")
            or result.get("already_starred")
            or result.get("already_unstarred")
        )

    def github_star_sync_record(repo: object, result: object) -> dict[str, object]:
        payload = dict(result if isinstance(result, dict) else {})
        if isinstance(repo, dict):
            full_name = normalize(repo.get("full_name"))
            url = normalize(repo.get("url"))
            if full_name:
                payload["full_name"] = full_name
            if url:
                payload["url"] = url
        return payload

    def json_error(message: str, status: int, code: str | None = None) -> JsonResult:
        return JsonResult(error_payload(message, code), status)

    def exception_to_error(route: Route, path: str, exc: Exception) -> JsonResult:
        raw_message = normalize(str(exc))
        if isinstance(exc, LocalAPIError):
            status = int(getattr(exc, "status", route.error_status) or route.error_status)
            code = normalize(getattr(exc, "code", "")) or ("not_found" if status == 404 else (route.error_code or "invalid_request"))
            logger.warning("http_request_rejected path=%s code=%s error=%s", path, code, raw_message)
            return json_error(localize_user_message(normalize, raw_message, "请求处理失败。"), status, code)
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
            raise LocalAPIError(
                localize_user_message(normalize, str(exc), "未找到对应的关键词发现任务。"),
                status=404,
                code="not_found",
            ) from exc
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
                raise LocalAPIError(localize_user_message(normalize, str(exc), "缺少仓库信息。")) from exc
            if github_star_sync and not (
                github_star_sync.get("ok")
                or github_star_sync.get("already_starred")
                or github_star_sync.get("already_unstarred")
            ):
                return JsonResult(github_star_sync, 400)
        try:
            set_repo_state(state_key, enabled, payload.get("repo"))
        except ValueError as exc:
            raise LocalAPIError(localize_user_message(normalize, str(exc), "请求处理失败。")) from exc
        return {
            "ok": True,
            "user_state": export_user_state(),
            "github_star_sync": github_star_sync,
        }

    def handle_post_state_batch(_handler, _parsed, payload):
        state_key = normalize(payload.get("state"))
        enabled = as_bool(payload.get("enabled"), True)
        repos = payload.get("repos")
        if not isinstance(repos, list):
            raise LocalAPIError("缺少仓库列表。")

        github_star_syncs: list[dict[str, object]] = []
        processed_repos = repos
        if state_key == "favorites":
            processed_repos = []
            for repo in repos:
                try:
                    github_star_sync = sync_favorite_repo(repo, enabled)
                except ValueError as exc:
                    error = localize_user_message(normalize, str(exc), "请求处理失败。")
                    if processed_repos:
                        set_repo_state_batch(state_key, enabled, processed_repos)
                    return JsonResult(
                        {
                            "ok": False,
                            "processed_count": len(processed_repos),
                            "user_state": export_user_state(),
                            "github_star_syncs": github_star_syncs,
                            "error": error,
                        },
                        400,
                    )
                if github_star_sync is not None:
                    if not github_star_sync_ok(github_star_sync):
                        if processed_repos:
                            set_repo_state_batch(state_key, enabled, processed_repos)
                        return JsonResult(
                            {
                                "ok": False,
                                "processed_count": len(processed_repos),
                                "user_state": export_user_state(),
                                "github_star_syncs": github_star_syncs,
                                "error": localize_user_message(normalize, github_star_sync.get("error"), "请求处理失败。"),
                            },
                            400,
                        )
                    github_star_syncs.append(github_star_sync_record(repo, github_star_sync))
                processed_repos.append(repo)

        try:
            processed = set_repo_state_batch(state_key, enabled, processed_repos)
        except ValueError as exc:
            return JsonResult(
                {
                    "ok": False,
                    "processed_count": int(getattr(exc, "processed_count", 0) or 0),
                    "user_state": export_user_state(),
                    "github_star_syncs": github_star_syncs,
                    "error": localize_user_message(normalize, str(exc), "请求处理失败。"),
                },
                400,
            )

        return {
            "ok": True,
            "processed_count": len(processed),
            "user_state": export_user_state(),
            "github_star_syncs": github_star_syncs,
        }

    def handle_post_import(_handler, _parsed, payload):
        try:
            result = import_user_state(payload)
        except ValueError as exc:
            raise LocalAPIError(localize_user_message(normalize, str(exc), "导入失败。")) from exc
        return {"ok": True, "message": "用户数据已导入", **result}

    def handle_post_settings(_handler, _parsed, payload):
        try:
            requested = merge_settings(payload, settings)
        except ValueError as exc:
            raise LocalAPIError(localize_user_message(normalize, str(exc), "保存设置失败。")) from exc
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
            f"设置已保存，端口将在重启后切换为 {settings.get('port', 8080)}"
            if restart_required
            else "设置已保存"
        )
        return {"ok": True, "message": message, "settings": sanitize_settings(True)}

    def handle_post_token_status(_handler, _parsed, payload):
        token = payload.get("github_token") if isinstance(payload, dict) and "github_token" in payload else None
        status = validate_github_token(token)
        return {"ok": True, "status": status}

    def handle_post_refresh(_handler, _parsed, _payload):
        if start_refresh_async("manual"):
            return {"ok": True, "message": "已开始后台刷新"}
        return json_error("后台刷新已在进行中。", 409, "refresh_in_progress")

    def handle_post_chatgpt_open(_handler, _parsed, payload):
        ok, message = open_chatgpt_target(payload.get("mode", "web"), payload.get("prompt", ""))
        return JsonResult({"ok": ok, "message": message}, 200 if ok else 400)

    def handle_post_open_external(_handler, _parsed, payload):
        url = normalize(payload.get("url"))
        if not url:
            raise LocalAPIError("缺少链接地址。")
        opened = open_external_url(url)
        return JsonResult({"ok": opened, "url": url}, 200 if opened else 500)

    def handle_post_clear_favorite_updates(_handler, _parsed, _payload):
        clear_favorite_updates()
        return {
            "ok": True,
            "message": "已清空关注更新记录",
            "user_state": export_user_state(),
        }

    def handle_post_discover(_handler, _parsed, payload):
        try:
            job = start_discovery_job(payload)
        except ValueError as exc:
            raise LocalAPIError(localize_user_message(normalize, str(exc), "开始搜索失败。")) from exc
        return {"ok": True, "message": "搜索已开始", "job": job}

    def handle_post_discovery_cancel(_handler, _parsed, payload):
        try:
            job = cancel_discovery_job(normalize(payload.get("id")))
        except ValueError as exc:
            raise LocalAPIError(localize_user_message(normalize, str(exc), "取消搜索失败。")) from exc
        return {"ok": True, "message": "已发送取消请求", "job": job}

    def handle_post_discovery_clear(_handler, _parsed, _payload):
        discovery_state = clear_discovery_results()
        return {"ok": True, "message": "已清空本次搜索结果", "discovery_state": discovery_state}

    def handle_post_window_open(_handler, _parsed, _payload):
        return {"ok": True, "opened": open_main_window()}

    def handle_post_window_exit(_handler, _parsed, _payload):
        exit_app()
        return {"ok": True, "message": "正在退出程序"}

    def handle_post_sync_stars(_handler, _parsed, _payload):
        try:
            starred = fetch_user_starred()
        except ValueError as exc:
            raise LocalAPIError(normalize(str(exc)) or "请先在设置中配置 GitHub Token。", code="github_token_missing") from exc
        summary = sync_local_favorites_with_starred(starred)
        total = int(summary.get("total") or 0)
        added = int(summary.get("added") or 0)
        removed = int(summary.get("removed") or 0)
        message = f"GitHub 星标已同步：共 {total} 个，新增 {added} 个，移除 {removed} 个"
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
        "/api/state/batch": Route(handle_post_state_batch, loopback_only=True, control_only=True, json_body=True),
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
            self.send_json(error_payload("该操作仅允许从本机访问。", "loopback_only"), 403)
            return False

        def require_control_token(self) -> bool:
            expected = normalize(control_token_getter())
            if not expected:
                return True
            actual = normalize(self.headers.get("X-GitSonar-Control", ""))
            if actual == expected:
                return True
            self.send_json(error_payload("缺少控制令牌或控制令牌无效。", "invalid_control_token"), 403)
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
                raise InvalidJsonBodyError("请求体必须是 JSON 对象。")
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
                return self.send_json(error_payload("接口不存在。", "not_found"), 404)
            return self.execute_route(route, parsed)

        def do_POST(self):
            parsed = urlparse(self.path)
            route = POST_ROUTES.get(parsed.path)
            if route is None:
                return self.send_json(error_payload("接口不存在。", "not_found"), 404)
            return self.execute_route(route, parsed)

    return AppHandler
