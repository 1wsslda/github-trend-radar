#!/usr/bin/env python3
from __future__ import annotations

import os
from types import SimpleNamespace


def make_diagnostics_runtime(
    *,
    app_name: str,
    runtime_root: str,
    status_path: str,
    sanitize_settings,
    current_port,
    validate_github_token,
    load_json_file,
    session,
    api_timeout,
    trending_timeout,
    tcp_port_open,
    iso_now,
):
    def item(key: str, title: str, state: str, summary: str, *, detail: str = "", suggestion: str = "") -> dict[str, object]:
        return {
            "key": key,
            "title": title,
            "state": state,
            "summary": summary,
            "detail": detail,
            "suggestion": suggestion,
        }

    def token_diagnostic() -> dict[str, object]:
        status = validate_github_token()
        state = str(status.get("state") or "").strip()
        summary = str(status.get("message") or "未执行 Token 检查。").strip()
        if state in {"success"}:
            level = "ok"
        elif state in {"empty", "insufficient"}:
            level = "warn"
        else:
            level = "error"
        login = str(status.get("login") or "").strip()
        detail = f"GitHub 账号：{login}" if login else ""
        suggestion = ""
        if state == "empty":
            suggestion = "需要稳定详情、发现和星标同步时，再到设置里显式配置 GitHub Token。"
        elif state == "invalid":
            suggestion = "请更新或重新生成 GitHub Token，然后重新运行诊断。"
        elif state == "insufficient":
            suggestion = "当前 Token 可用于部分 API，但 GitHub 星标同步权限不足。"
        return item("github_token", "GitHub Token", level, summary, detail=detail, suggestion=suggestion)

    def loopback_diagnostic() -> dict[str, object]:
        port = int(current_port())
        is_open = tcp_port_open("127.0.0.1", port)
        return item(
            "loopback_port",
            "本地回环端口",
            "ok" if is_open else "error",
            f"127.0.0.1:{port} {'可访问' if is_open else '不可访问'}",
            suggestion="如果端口不可访问，请先检查本地进程是否仍在运行，或重启应用。" if not is_open else "",
        )

    def status_file_diagnostic() -> dict[str, object]:
        exists = os.path.exists(status_path)
        payload = load_json_file(status_path, {}) if exists else {}
        refreshing = bool(payload.get("refreshing")) if isinstance(payload, dict) else False
        updated_at = str(payload.get("updated_at") or payload.get("fetched_at") or "").strip() if isinstance(payload, dict) else ""
        return item(
            "status_file",
            "运行状态文件",
            "ok" if exists else "warn",
            "状态文件可读取。" if exists else "状态文件尚未生成。",
            detail=f"最近更新时间：{updated_at or '未知'}；后台刷新：{'是' if refreshing else '否'}",
            suggestion="如果状态文件长期不存在，先尝试手动刷新一次。" if not exists else "",
        )

    def proxy_diagnostic() -> dict[str, object]:
        settings = sanitize_settings(False)
        effective_proxy = str(settings.get("effective_proxy") or "").strip()
        proxy_source = str(settings.get("proxy_source") or "").strip()
        has_proxy = bool(effective_proxy)
        summary = f"{'已启用' if has_proxy else '未启用'}代理"
        detail = f"来源：{proxy_source or 'none'}"
        if effective_proxy:
            detail = f"{detail}；当前代理：{effective_proxy}"
        suggestion = "如果 GitHub 无法访问，可先确认本机网络环境，再检查代理地址是否可用。"
        return item("proxy", "代理配置", "ok" if has_proxy else "warn", summary, detail=detail, suggestion=suggestion)

    def runtime_root_diagnostic() -> dict[str, object]:
        exists = os.path.isdir(runtime_root)
        writable = os.access(runtime_root, os.W_OK) if exists else False
        state = "ok" if exists and writable else "error"
        summary = "运行目录可写。" if state == "ok" else "运行目录不可写或不存在。"
        suggestion = "请检查运行目录权限，避免状态文件、缓存和导出失败。"
        return item("runtime_root", f"{app_name} 运行目录", state, summary, detail=runtime_root, suggestion=suggestion if state != "ok" else "")

    def check_url(title: str, key: str, url: str, timeout) -> dict[str, object]:
        try:
            response = session.get(url, timeout=timeout, headers={"Accept": "application/vnd.github+json"})
            response.raise_for_status()
            state = "ok"
            summary = f"{title} 可访问。"
            detail = ""
            if "rate_limit" in url and hasattr(response, "json"):
                payload = response.json()
                remaining = payload.get("rate", {}).get("remaining")
                reset = payload.get("rate", {}).get("reset")
                if remaining is not None:
                    detail = f"剩余额度：{remaining}"
                    if reset:
                        detail = f"{detail}；重置时间戳：{reset}"
            return item(key, title, state, summary, detail=detail)
        except Exception as exc:
            return item(
                key,
                title,
                "error",
                f"{title} 不可访问。",
                detail=str(exc),
                suggestion="请优先检查网络、代理和 GitHub 可达性。",
            )

    def run_diagnostics() -> dict[str, object]:
        items = [
            runtime_root_diagnostic(),
            loopback_diagnostic(),
            status_file_diagnostic(),
            proxy_diagnostic(),
            token_diagnostic(),
            check_url("GitHub API", "github_api", "https://api.github.com/rate_limit", api_timeout),
            check_url("GitHub Trending", "github_trending", "https://github.com/trending", trending_timeout),
        ]
        return {
            "generated_at": iso_now(),
            "items": items,
            "has_errors": any(entry["state"] == "error" for entry in items),
        }

    return SimpleNamespace(run_diagnostics=run_diagnostics)


__all__ = ["make_diagnostics_runtime"]
