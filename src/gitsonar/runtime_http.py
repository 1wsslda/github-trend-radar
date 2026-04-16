#!/usr/bin/env python3
from __future__ import annotations

import json
import logging
from http.server import SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

logger = logging.getLogger(__name__)


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
    run_discovery_search,
    run_saved_discovery_query,
    start_discovery_job,
    start_saved_discovery_job,
    get_discovery_job,
    cancel_discovery_job,
    delete_saved_discovery_query,
    clear_discovery_results,
    export_discovery_state,
    export_active_discovery_job,
    open_main_window,
    hide_main_window,
    exit_app,
    star_repo,
    fetch_user_starred,
    batch_add_favorites,
):
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
            self.send_json({"ok": False, "error": "该操作仅允许本机访问。"}, 403)
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

        def read_json(self) -> dict[str, object]:
            raw_length = self.headers.get("Content-Length", "0")
            try:
                length = max(0, int(raw_length))
            except (TypeError, ValueError):
                logger.warning("收到无效 Content-Length: %r，按 0 处理", raw_length)
                length = 0
            raw_body = self.rfile.read(length).decode("utf-8") if length else "{}"
            if not raw_body.strip():
                return {}
            try:
                payload = json.loads(raw_body)
            except json.JSONDecodeError as exc:
                raise ValueError(f"请求体不是有效的 JSON: {exc.msg}") from exc
            if not isinstance(payload, dict):
                raise ValueError("请求体必须是 JSON 对象")
            return payload

        def do_GET(self):
            parsed = urlparse(self.path)

            if parsed.path == "/api/settings":
                return self.send_json(sanitize_settings(self.is_loopback_request()))

            if parsed.path == "/api/status":
                return self.send_json(load_json_file(status_path, {}))

            if parsed.path == "/api/repo-details":
                params = parse_qs(parsed.query)
                owner = (params.get("owner") or [""])[0]
                name = (params.get("name") or [""])[0]
                try:
                    details = fetch_repo_details(owner, name)
                except Exception as exc:
                    return self.send_json({"ok": False, "error": str(exc)}, 500)
                return self.send_json({"ok": True, "details": details})

            if parsed.path == "/api/discovery":
                return self.send_json({
                    "ok": True,
                    "discovery_state": export_discovery_state(),
                    "active_job": export_active_discovery_job(),
                })

            if parsed.path == "/api/discovery/job":
                params = parse_qs(parsed.query)
                try:
                    job = get_discovery_job((params.get("id") or [""])[0])
                except Exception as exc:
                    return self.send_json({"ok": False, "error": str(exc)}, 404)
                return self.send_json({"ok": True, "job": job})

            if parsed.path == "/api/export":
                if not self.is_loopback_request():
                    return self.send_json({"ok": False, "error": "该操作仅允许本机访问。"}, 403)
                try:
                    body = json.dumps(export_user_state(), ensure_ascii=False, indent=2).encode("utf-8")
                except Exception as exc:
                    return self.send_json({"ok": False, "error": str(exc)}, 500)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Content-Disposition", 'attachment; filename="gitsonar_backup.json"')
                self.end_headers()
                self.wfile.write(body)
                return

            if parsed.path in {"/", "/trending.html"}:
                self.path = "/trending.html"
                return super().do_GET()

            return self.send_json({"ok": False, "error": "未知接口。"}, 404)

        def do_POST(self):
            parsed = urlparse(self.path)
            if not self.require_loopback():
                return

            if parsed.path == "/api/state":
                try:
                    payload = self.read_json()
                    set_repo_state(
                        normalize(payload.get("state")),
                        as_bool(payload.get("enabled"), True),
                        payload.get("repo"),
                    )
                except Exception as exc:
                    return self.send_json({"ok": False, "error": str(exc)}, 400)
                return self.send_json({"ok": True, "user_state": export_user_state()})

            if parsed.path == "/api/import":
                try:
                    result = import_user_state(self.read_json())
                except Exception as exc:
                    return self.send_json({"ok": False, "error": str(exc)}, 400)
                return self.send_json({
                    "ok": True,
                    "message": "用户状态已导入",
                    **result,
                })

            if parsed.path == "/api/settings":
                try:
                    requested = normalize_settings(self.read_json())
                    with settings_lock:
                        settings.clear()
                        settings.update(requested)
                        save_settings(settings)
                        apply_runtime_settings()
                except Exception as exc:
                    return self.send_json({"ok": False, "error": str(exc)}, 400)

                try:
                    update_auto_start(bool(settings.get("auto_start")))
                except Exception as exc:
                    logger.warning("更新开机启动项失败（设置已保存）: %s", exc)

                restart_required = bool(
                    clamp_int(settings.get("port", 8080), 8080, 1, 65535) != current_port()
                )
                if restart_required:
                    message = f"设置已保存，端口会在重启应用后切换到 {settings.get('port', 8080)}。"
                else:
                    message = "设置已保存。"
                return self.send_json({
                    "ok": True,
                    "message": message,
                    "settings": sanitize_settings(True),
                })

            if parsed.path == "/api/refresh":
                if start_refresh_async("manual"):
                    return self.send_json({"ok": True, "message": "已开始后台刷新。"})
                return self.send_json({"ok": False, "error": "后台正在刷新，请稍后。"}, 409)

            if parsed.path == "/api/chatgpt/open":
                try:
                    payload = self.read_json()
                    ok, message = open_chatgpt_target(payload.get("mode", "web"), payload.get("prompt", ""))
                except Exception as exc:
                    return self.send_json({"ok": False, "error": str(exc)}, 400)
                return self.send_json({"ok": ok, "message": message}, 200 if ok else 400)

            if parsed.path == "/api/open-external":
                try:
                    payload = self.read_json()
                    url = normalize(payload.get("url"))
                    if not url:
                        raise ValueError("缺少链接地址。")
                    opened = open_external_url(url)
                except Exception as exc:
                    return self.send_json({"ok": False, "error": str(exc)}, 400)
                return self.send_json({"ok": opened, "url": url}, 200 if opened else 500)

            if parsed.path == "/api/favorite-updates/clear":
                clear_favorite_updates()
                return self.send_json({
                    "ok": True,
                    "message": "已清空收藏更新记录。",
                    "user_state": export_user_state(),
                })

            if parsed.path == "/api/discover":
                try:
                    payload = self.read_json()
                    job = start_discovery_job(payload)
                except Exception as exc:
                    return self.send_json({"ok": False, "error": str(exc)}, 400)
                return self.send_json({
                    "ok": True,
                    "message": "关键词发现任务已开始",
                    "job": job,
                })

            if parsed.path == "/api/discovery/run-saved":
                try:
                    payload = self.read_json()
                    job = start_saved_discovery_job(normalize(payload.get("id")))
                except Exception as exc:
                    return self.send_json({"ok": False, "error": str(exc)}, 400)
                return self.send_json({
                    "ok": True,
                    "message": "已开始重新运行保存的搜索",
                    "job": job,
                })

            if parsed.path == "/api/discovery/cancel":
                try:
                    payload = self.read_json()
                    job = cancel_discovery_job(normalize(payload.get("id")))
                except Exception as exc:
                    return self.send_json({"ok": False, "error": str(exc)}, 400)
                return self.send_json({
                    "ok": True,
                    "message": "已发送取消请求",
                    "job": job,
                })

            if parsed.path == "/api/discovery/delete":
                try:
                    payload = self.read_json()
                    discovery_state = delete_saved_discovery_query(normalize(payload.get("id")))
                except Exception as exc:
                    return self.send_json({"ok": False, "error": str(exc)}, 400)
                return self.send_json({
                    "ok": True,
                    "message": "已删除保存的搜索",
                    "discovery_state": discovery_state,
                })

            if parsed.path == "/api/discovery/clear":
                discovery_state = clear_discovery_results()
                return self.send_json({
                    "ok": True,
                    "message": "已清空本次关键词发现结果",
                    "discovery_state": discovery_state,
                })

            if parsed.path == "/api/window/open":
                return self.send_json({"ok": True, "opened": open_main_window()})

            if parsed.path == "/api/window/hide":
                hidden = hide_main_window()
                return self.send_json({
                    "ok": hidden,
                    "message": "已隐藏到系统托盘。" if hidden else "当前窗口无法隐藏。",
                })

            if parsed.path == "/api/window/exit":
                exit_app()
                return self.send_json({
                    "ok": True,
                    "message": "正在退出程序。",
                })

            if parsed.path == "/api/sync-stars":
                try:
                    starred = fetch_user_starred()
                    total, added = batch_add_favorites(starred)
                except Exception as exc:
                    return self.send_json({"ok": False, "error": str(exc)}, 400)
                skipped = total - added
                msg = f"同步完成：共 {total} 个星标仓库，新增 {added} 个"
                if skipped:
                    msg += f"（{skipped} 个已在收藏中）"
                return self.send_json({
                    "ok": True,
                    "total": total,
                    "added": added,
                    "message": msg,
                    "user_state": export_user_state(),
                })

            if parsed.path == "/api/star":
                try:
                    payload = self.read_json()
                    owner = normalize(payload.get("owner", ""))
                    name = normalize(payload.get("name", ""))
                    if not owner or not name:
                        raise ValueError("缺少仓库信息")
                    result = star_repo(owner, name)
                except Exception as exc:
                    return self.send_json({"ok": False, "error": str(exc)}, 400)
                status = 200 if (result.get("ok") or result.get("already_starred")) else 400
                return self.send_json(result, status)

            return self.send_json({"ok": False, "error": "未知接口。"}, 404)

    return AppHandler
