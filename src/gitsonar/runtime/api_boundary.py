#!/usr/bin/env python3
from __future__ import annotations

import json
from types import SimpleNamespace


def _clone(payload: object) -> object:
    return json.loads(json.dumps(payload, ensure_ascii=False))


def make_api_boundary_runtime(
    *,
    periods,
    current_snapshot_getter,
    export_user_state,
    export_discovery_state,
    sanitize_settings,
    status_getter,
    normalize,
):
    period_keys = [normalize(period.get("key")) for period in periods if isinstance(period, dict) and normalize(period.get("key"))]
    state_keys = {"favorites", "watch_later", "read", "ignored"}

    def current_snapshot() -> dict[str, object]:
        snapshot = current_snapshot_getter() if callable(current_snapshot_getter) else {}
        return snapshot if isinstance(snapshot, dict) else {}

    def user_state() -> dict[str, object]:
        state = export_user_state() if callable(export_user_state) else {}
        return state if isinstance(state, dict) else {}

    def discovery_state() -> dict[str, object]:
        state = export_discovery_state() if callable(export_discovery_state) else {}
        return state if isinstance(state, dict) else {}

    def normalized_repo(repo: object) -> dict[str, object] | None:
        if not isinstance(repo, dict):
            return None
        url = normalize(repo.get("url"))
        full_name = normalize(repo.get("full_name"))
        if not url or not full_name:
            return None
        clean = dict(repo)
        clean["url"] = url
        clean["full_name"] = full_name
        return clean

    def dedupe_repos(items: object) -> list[dict[str, object]]:
        repos: list[dict[str, object]] = []
        seen: set[str] = set()
        if not isinstance(items, list):
            return repos
        for item in items:
            clean = normalized_repo(item)
            if not clean or clean["url"] in seen:
                continue
            repos.append(clean)
            seen.add(clean["url"])
        return repos

    def repo_records() -> dict[str, dict[str, object]]:
        records = user_state().get("repo_records", {})
        if not isinstance(records, dict):
            return {}
        return {url: clean for url, item in records.items() if normalize(url) and (clean := normalized_repo(item))}

    def repos_for_state(state_key: str) -> list[dict[str, object]]:
        clean_key = normalize(state_key)
        if clean_key not in state_keys:
            return []
        records = repo_records()
        urls = user_state().get(clean_key, [])
        if not isinstance(urls, list):
            return []
        return [records[url] for url in urls if url in records]

    def all_repos() -> list[dict[str, object]]:
        groups: list[dict[str, object]] = []
        snapshot = current_snapshot()
        for key in period_keys:
            groups.extend(dedupe_repos(snapshot.get(key, [])))
        groups.extend(dedupe_repos(discovery_state().get("last_results", [])))
        groups.extend(repo_records().values())
        return dedupe_repos(groups)

    def filter_repos(repos: list[dict[str, object]], q: str) -> list[dict[str, object]]:
        clean_q = normalize(q).lower()
        if not clean_q:
            return repos
        matched: list[dict[str, object]] = []
        for repo in repos:
            haystack = " ".join(
                normalize(value).lower()
                for value in (
                    repo.get("full_name"),
                    repo.get("description"),
                    repo.get("description_raw"),
                    repo.get("language"),
                    " ".join(repo.get("topics", [])) if isinstance(repo.get("topics"), list) else "",
                )
            )
            if clean_q in haystack:
                matched.append(repo)
        return matched

    def export_repos(*, view: object = "", state: object = "", q: object = "") -> dict[str, object]:
        clean_view = normalize(view).lower()
        clean_state = normalize(state).lower()
        if clean_state in state_keys:
            repos = repos_for_state(clean_state)
        elif clean_view in period_keys:
            repos = dedupe_repos(current_snapshot().get(clean_view, []))
        elif clean_view in {"discover", "discovery"}:
            repos = dedupe_repos(discovery_state().get("last_results", []))
            clean_view = "discover"
        else:
            repos = all_repos()
            clean_view = clean_view or "all"
        repos = filter_repos(repos, normalize(q))
        return {
            "ok": True,
            "view": clean_view,
            "state": clean_state if clean_state in state_keys else "",
            "q": normalize(q),
            "count": len(repos),
            "repos": _clone(repos),
        }

    def export_updates() -> dict[str, object]:
        updates = user_state().get("favorite_updates", [])
        clean_updates = [dict(item) for item in updates if isinstance(item, dict)] if isinstance(updates, list) else []
        return {"ok": True, "count": len(clean_updates), "updates": _clone(clean_updates)}

    def export_discovery_views() -> dict[str, object]:
        views = discovery_state().get("saved_views", [])
        clean_views = [dict(item) for item in views if isinstance(item, dict)] if isinstance(views, list) else []
        return {"ok": True, "count": len(clean_views), "views": _clone(clean_views)}

    def export_bootstrap() -> dict[str, object]:
        state = user_state()
        discovery = discovery_state()
        repos = all_repos()
        updates = state.get("favorite_updates", [])
        views = discovery.get("saved_views", [])
        return {
            "ok": True,
            "settings": sanitize_settings(False) if callable(sanitize_settings) else {},
            "status": status_getter() if callable(status_getter) else {},
            "counts": {
                "repos": len(repos),
                "favorites": len(state.get("favorites", [])) if isinstance(state.get("favorites"), list) else 0,
                "watch_later": len(state.get("watch_later", [])) if isinstance(state.get("watch_later"), list) else 0,
                "read": len(state.get("read", [])) if isinstance(state.get("read"), list) else 0,
                "ignored": len(state.get("ignored", [])) if isinstance(state.get("ignored"), list) else 0,
                "favorite_updates": len(updates) if isinstance(updates, list) else 0,
            },
            "discovery": {
                "saved_view_count": len(views) if isinstance(views, list) else 0,
                "last_result_count": len(discovery.get("last_results", []))
                if isinstance(discovery.get("last_results"), list)
                else 0,
            },
        }

    return SimpleNamespace(
        export_bootstrap=export_bootstrap,
        export_repos=export_repos,
        export_updates=export_updates,
        export_discovery_views=export_discovery_views,
    )


__all__ = ["make_api_boundary_runtime"]
