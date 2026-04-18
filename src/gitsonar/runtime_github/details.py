#!/usr/bin/env python3
from __future__ import annotations

import base64


def build_details_api(*, deps, github_get):
    normalize = deps.normalize
    cached_repo_details = deps.cached_repo_details
    detail_fetch_lock = deps.detail_fetch_lock
    fetch_semaphore = deps.fetch_semaphore
    repo_api_url = deps.repo_api_url
    clamp_int = deps.clamp_int
    strip_markdown = deps.strip_markdown
    translate_text = deps.translate_text
    save_translation_cache = deps.save_translation_cache
    save_repo_details = deps.save_repo_details

    def fetch_repo_details(owner: str, name: str) -> dict[str, object]:
        owner = normalize(owner)
        name = normalize(name)
        if not owner or not name:
            raise ValueError("缺少仓库参数")

        cache_key = f"{owner}/{name}".lower()
        cached = cached_repo_details(cache_key)
        if cached is not None:
            return cached

        with detail_fetch_lock(cache_key):
            cached = cached_repo_details(cache_key)
            if cached is not None:
                return cached

            with fetch_semaphore:
                repo = github_get(f"{repo_api_url}/{owner}/{name}").json()
                try:
                    readme = github_get(f"{repo_api_url}/{owner}/{name}/readme").json()
                    if readme.get("encoding") == "base64":
                        content = base64.b64decode(readme.get("content", "")).decode("utf-8", errors="ignore")
                    else:
                        content = ""
                    summary = strip_markdown(content)[:900]
                except Exception:
                    summary = ""

            raw_description = normalize(repo.get("description"))
            raw_summary = normalize(summary)
            details = {
                "full_name": normalize(repo.get("full_name")) or f"{owner}/{name}",
                "description": translate_text(raw_description),
                "description_raw": raw_description,
                "license": normalize(
                    repo.get("license", {}).get("spdx_id") if isinstance(repo.get("license"), dict) else ""
                )
                or "未标注",
                "homepage": normalize(repo.get("homepage")),
                "default_branch": normalize(repo.get("default_branch")),
                "updated_at": normalize(repo.get("updated_at")),
                "pushed_at": normalize(repo.get("pushed_at")),
                "topics": repo.get("topics", []) if isinstance(repo.get("topics"), list) else [],
                "html_url": normalize(repo.get("html_url")) or f"https://github.com/{owner}/{name}",
                "stars": clamp_int(repo.get("stargazers_count"), 0, 0),
                "forks": clamp_int(repo.get("forks_count"), 0, 0),
                "watchers": clamp_int(repo.get("watchers_count"), 0, 0),
                "open_issues": clamp_int(repo.get("open_issues_count"), 0, 0),
                "readme_summary": translate_text(raw_summary),
                "readme_summary_raw": raw_summary,
            }
            save_translation_cache()
            save_repo_details(cache_key, details)
            return dict(details)

    return {"fetch_repo_details": fetch_repo_details}
