#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from types import SimpleNamespace
from urllib.parse import urlparse

DISCOVERY_RANKING_PROFILES = {'balanced', 'hot', 'fresh', 'builder', 'trend'}


def make_state_runtime(
    *,
    settings,
    user_state,
    discovery_state,
    state_lock,
    discovery_lock,
    current_snapshot_getter,
    sync_repo_records_callback,
    user_state_path,
    discovery_state_path,
    latest_snapshot_path,
    periods,
    normalize,
    clamp_int,
    as_bool,
    iso_now,
    load_json_file,
    atomic_write_json,
    apply_repo_translation,
):
    SETTINGS = settings
    USER_STATE = user_state
    DISCOVERY_STATE = discovery_state
    STATE_LOCK = state_lock
    DISCOVERY_LOCK = discovery_lock
    current_snapshot = current_snapshot_getter
    sync_repo_records = sync_repo_records_callback
    USER_STATE_PATH = user_state_path
    DISCOVERY_STATE_PATH = discovery_state_path
    LATEST_SNAPSHOT_PATH = latest_snapshot_path
    PERIODS = periods
    def default_user_state() -> dict[str, object]:
        return {'favorites': [], 'watch_later': [], 'read': [], 'ignored': [], 'repo_records': {}, 'favorite_watch': {}, 'favorite_updates': []}

    def default_discovery_state() -> dict[str, object]:
        return {
            'saved_queries': [],
            'last_query': {},
            'last_results': [],
            'last_related_terms': [],
            'last_generated_queries': [],
            'last_translated_query': '',
            'last_warnings': [],
            'last_run_at': '',
            'last_error': '',
        }


    DISCOVERY_RANKING_PROFILES = {'balanced', 'hot', 'fresh', 'builder', 'trend'}

    def normalize_discovery_ranking_profile(value: object) -> str:
        clean = normalize(value).lower()
        return clean if clean in DISCOVERY_RANKING_PROFILES else 'balanced'

    def discovery_query_id(query: str, language: str, auto_expand: bool, ranking_profile: str = 'balanced') -> str:
        payload = f'{normalize(query)}\n{normalize(language)}\n{int(bool(auto_expand))}\n{normalize_discovery_ranking_profile(ranking_profile)}'
        return hashlib.sha1(payload.encode('utf-8')).hexdigest()[:16]

    def normalize_discovery_query(payload: object) -> dict[str, object] | None:
        raw = payload if isinstance(payload, dict) else {}
        query = normalize(raw.get('query'))
        if not query:
            return None
        language = normalize(raw.get('language'))
        auto_expand = as_bool(raw.get('auto_expand'), True)
        ranking_profile = normalize_discovery_ranking_profile(raw.get('ranking_profile'))
        default_limit = clamp_int(SETTINGS.get('result_limit', 20), 20, 5, 50) if SETTINGS else 20
        return {
            'id': normalize(raw.get('id')) or discovery_query_id(query, language, auto_expand, ranking_profile),
            'query': query,
            'language': language,
            'limit': clamp_int(raw.get('limit'), default_limit, 5, 50),
            'auto_expand': auto_expand,
            'ranking_profile': ranking_profile,
            'created_at': normalize(raw.get('created_at')) or iso_now(),
            'last_run_at': normalize(raw.get('last_run_at')),
        }

    def normalize_repo(repo: object) -> dict[str, object] | None:
        if not isinstance(repo, dict):
            return None
        full_name = normalize(repo.get('full_name'))
        url = normalize(repo.get('url'))
        if not full_name or not url or '/' not in full_name:
            return None
        owner, name = full_name.split('/', 1)
        gained = clamp_int(repo.get('gained'), 0, 0)
        gained_text = normalize(repo.get('gained_text'))
        growth_source = normalize(repo.get('growth_source')).lower()
        if growth_source not in {'trending', 'estimated', 'unavailable'}:
            growth_source = 'trending' if gained_text or gained > 0 else 'unavailable'
        return {
            'full_name': full_name,
            'owner': owner,
            'name': name,
            'url': url,
            'description': normalize(repo.get('description')),
            'description_raw': normalize(repo.get('description_raw') or repo.get('description')),
            'language': normalize(repo.get('language')),
            'stars': clamp_int(repo.get('stars'), 0, 0),
            'forks': clamp_int(repo.get('forks'), 0, 0),
            'gained': gained,
            'gained_text': gained_text,
            'growth_source': growth_source,
            'rank': clamp_int(repo.get('rank'), 0, 0),
            'period_key': normalize(repo.get('period_key')) or 'daily',
            'source_label': normalize(repo.get('source_label')) or 'GitHub API',
            'updated_at': normalize(repo.get('updated_at')),
            'pushed_at': normalize(repo.get('pushed_at')),
            'topics': [normalize(item) for item in repo.get('topics', []) if normalize(item)] if isinstance(repo.get('topics'), list) else [],
            'discover_source': normalize(repo.get('discover_source')),
            'trending_hit': as_bool(repo.get('trending_hit'), False),
            'relevance_score': clamp_int(repo.get('relevance_score'), 0, 0, 100),
            'hot_score': clamp_int(repo.get('hot_score'), 0, 0, 100),
            'composite_score': clamp_int(repo.get('composite_score'), 0, 0, 100),
            'matched_terms': [normalize(item) for item in repo.get('matched_terms', []) if normalize(item)] if isinstance(repo.get('matched_terms'), list) else [],
            'match_reasons': [normalize(item) for item in repo.get('match_reasons', []) if normalize(item)] if isinstance(repo.get('match_reasons'), list) else [],
        }

    def repo_from_url(url: object) -> dict[str, object] | None:
        raw = normalize(url)
        if not raw:
            return None
        parsed = urlparse(raw)
        parts = [part for part in parsed.path.split('/') if part]
        if len(parts) < 2:
            return None
        full_name = f'{parts[0]}/{parts[1]}'
        return normalize_repo({'full_name': full_name, 'url': f'https://github.com/{full_name}'})

    def normalize_watch_entry(payload: object) -> dict[str, object] | None:
        raw = payload if isinstance(payload, dict) else {}
        full_name = normalize(raw.get('full_name'))
        url = normalize(raw.get('url'))
        if not full_name or not url:
            return None
        return {
            'full_name': full_name,
            'url': url,
            'stars': clamp_int(raw.get('stars'), 0, 0),
            'forks': clamp_int(raw.get('forks'), 0, 0),
            'open_issues': clamp_int(raw.get('open_issues'), 0, 0),
            'updated_at': normalize(raw.get('updated_at')),
            'pushed_at': normalize(raw.get('pushed_at')),
            'latest_release_tag': normalize(raw.get('latest_release_tag')),
            'latest_release_published_at': normalize(raw.get('latest_release_published_at')),
            'release_checked_at': normalize(raw.get('release_checked_at')),
            'checked_at': normalize(raw.get('checked_at')),
        }

    def normalize_favorite_update(payload: object) -> dict[str, object] | None:
        raw = payload if isinstance(payload, dict) else {}
        full_name = normalize(raw.get('full_name'))
        url = normalize(raw.get('url'))
        if not full_name or not url:
            return None
        changes = [normalize(item) for item in raw.get('changes', []) if normalize(item)]
        if not changes:
            return None
        return {
            'id': normalize(raw.get('id')) or f'{full_name}:{normalize(raw.get("checked_at"))}',
            'full_name': full_name,
            'url': url,
            'checked_at': normalize(raw.get('checked_at')),
            'changes': changes,
            'stars': clamp_int(raw.get('stars'), 0, 0),
            'forks': clamp_int(raw.get('forks'), 0, 0),
            'latest_release_tag': normalize(raw.get('latest_release_tag')),
            'pushed_at': normalize(raw.get('pushed_at')),
        }

    def normalize_discovery_state(payload: object) -> dict[str, object]:
        raw = payload if isinstance(payload, dict) else {}
        state = default_discovery_state()
        saved_queries: list[dict[str, object]] = []
        seen_ids: set[str] = set()
        for item in raw.get('saved_queries', []):
            clean = normalize_discovery_query(item)
            if clean and clean['id'] not in seen_ids:
                saved_queries.append(clean)
                seen_ids.add(clean['id'])
        state['saved_queries'] = saved_queries
        state['last_query'] = normalize_discovery_query(raw.get('last_query')) or {}
        state['last_results'] = [clean for item in raw.get('last_results', []) if (clean := normalize_repo(item))]
        state['last_related_terms'] = [normalize(item) for item in raw.get('last_related_terms', []) if normalize(item)][:12]
        state['last_generated_queries'] = [normalize(item) for item in raw.get('last_generated_queries', []) if normalize(item)][:12]
        state['last_translated_query'] = normalize(raw.get('last_translated_query'))
        state['last_warnings'] = [normalize(item) for item in raw.get('last_warnings', []) if normalize(item)][:8]
        state['last_run_at'] = normalize(raw.get('last_run_at'))
        state['last_error'] = normalize(raw.get('last_error'))
        return state

    def normalize_user_state(payload: object) -> dict[str, object]:
        raw = payload if isinstance(payload, dict) else {}
        state = default_user_state()
        for key in ('favorites', 'watch_later', 'read', 'ignored'):
            state[key] = list(dict.fromkeys(normalize(item) for item in raw.get(key, []) if normalize(item)))
        records = raw.get('repo_records', {}) if isinstance(raw.get('repo_records'), dict) else {}
        state['repo_records'] = {url: clean for url, repo in records.items() if (clean := normalize_repo(repo))}
        watch = raw.get('favorite_watch', {}) if isinstance(raw.get('favorite_watch'), dict) else {}
        state['favorite_watch'] = {url: clean for url, item in watch.items() if (clean := normalize_watch_entry(item))}
        favorite_updates: list[dict[str, object]] = []
        seen_update_ids: set[str] = set()
        for item in raw.get('favorite_updates', []):
            clean = normalize_favorite_update(item)
            if clean and clean['id'] not in seen_update_ids:
                favorite_updates.append(clean)
                seen_update_ids.add(clean['id'])
        state['favorite_updates'] = favorite_updates
        return state

    def load_user_state() -> dict[str, object]:
        state = normalize_user_state(load_json_file(USER_STATE_PATH, default_user_state()))
        if not os.path.exists(USER_STATE_PATH):
            atomic_write_json(USER_STATE_PATH, state)
        return state

    def save_user_state() -> None:
        atomic_write_json(USER_STATE_PATH, USER_STATE)

    def export_user_state() -> dict[str, object]:
        with STATE_LOCK:
            return json.loads(json.dumps(USER_STATE, ensure_ascii=False))

    def state_counts(state: dict[str, object]) -> dict[str, int]:
        return {
            'favorites': len(state.get('favorites', [])),
            'watch_later': len(state.get('watch_later', [])),
            'read': len(state.get('read', [])),
            'ignored': len(state.get('ignored', [])),
            'repo_records': len(state.get('repo_records', {})),
            'favorite_updates': len(state.get('favorite_updates', [])),
        }

    def ordered_unique_urls(*groups: list[str]) -> list[str]:
        seen: set[str] = set()
        merged: list[str] = []
        for group in groups:
            for item in group:
                clean = normalize(item)
                if clean and clean not in seen:
                    merged.append(clean)
                    seen.add(clean)
        return merged

    def merge_favorite_updates(*groups: list[dict[str, object]]) -> list[dict[str, object]]:
        merged: list[dict[str, object]] = []
        seen_ids: set[str] = set()
        for group in groups:
            for item in group:
                clean = normalize_favorite_update(item)
                if clean and clean['id'] not in seen_ids:
                    merged.append(clean)
                    seen_ids.add(clean['id'])
        return merged[:100]

    def coerce_import_user_state(payload: object) -> dict[str, object]:
        if isinstance(payload, dict):
            if isinstance(payload.get('data'), dict):
                raw_state = payload.get('data')
            elif isinstance(payload.get('user_state'), dict):
                raw_state = payload.get('user_state')
            else:
                raw_state = payload
        else:
            raw_state = {}
        state = normalize_user_state(raw_state)
        if not any(state.get(key) for key in ('favorites', 'watch_later', 'read', 'ignored')) and not state.get('repo_records'):
            raise ValueError('导入文件里没有可恢复的用户状态')
        return state

    def import_user_state(payload: object) -> dict[str, object]:
        mode = normalize(payload.get('mode') if isinstance(payload, dict) else '').lower()
        if mode not in {'merge', 'replace'}:
            mode = 'merge'
        imported = coerce_import_user_state(payload)
        with STATE_LOCK:
            before_counts = state_counts(USER_STATE)
            if mode == 'replace':
                next_state = imported
            else:
                next_state = default_user_state()
                for key in ('favorites', 'watch_later', 'read', 'ignored'):
                    next_state[key] = ordered_unique_urls(imported.get(key, []), USER_STATE.get(key, []))
                next_state['repo_records'] = dict(USER_STATE.get('repo_records', {}))
                next_state['repo_records'].update(imported.get('repo_records', {}))
                next_state['favorite_watch'] = dict(USER_STATE.get('favorite_watch', {}))
                next_state['favorite_watch'].update(imported.get('favorite_watch', {}))
                next_state['favorite_updates'] = merge_favorite_updates(
                    imported.get('favorite_updates', []),
                    USER_STATE.get('favorite_updates', []),
                )

            favorite_urls = set(next_state.get('favorites', []))
            next_state['favorite_watch'] = {
                url: item for url, item in next_state.get('favorite_watch', {}).items()
                if url in favorite_urls and normalize_watch_entry(item)
            }
            next_state['favorite_updates'] = [
                item for item in next_state.get('favorite_updates', [])
                if item.get('url') in favorite_urls
            ][:100]
            USER_STATE.clear()
            USER_STATE.update(normalize_user_state(next_state))
            save_user_state()
            after_counts = state_counts(USER_STATE)
        if callable(sync_repo_records):
            snapshot = current_snapshot() if callable(current_snapshot) else {}
            sync_repo_records(snapshot if isinstance(snapshot, dict) else {})
        return {
            'mode': mode,
            'before_counts': before_counts,
            'after_counts': after_counts,
            'user_state': export_user_state(),
        }

    def load_discovery_state() -> dict[str, object]:
        state = normalize_discovery_state(load_json_file(DISCOVERY_STATE_PATH, default_discovery_state()))
        if not os.path.exists(DISCOVERY_STATE_PATH):
            atomic_write_json(DISCOVERY_STATE_PATH, state)
        return state

    def save_discovery_state() -> None:
        atomic_write_json(DISCOVERY_STATE_PATH, DISCOVERY_STATE)

    def export_discovery_state() -> dict[str, object]:
        with DISCOVERY_LOCK:
            return json.loads(json.dumps(DISCOVERY_STATE, ensure_ascii=False))

    def clear_discovery_results() -> dict[str, object]:
        with DISCOVERY_LOCK:
            DISCOVERY_STATE['last_query'] = {}
            DISCOVERY_STATE['last_results'] = []
            DISCOVERY_STATE['last_related_terms'] = []
            DISCOVERY_STATE['last_generated_queries'] = []
            DISCOVERY_STATE['last_translated_query'] = ''
            DISCOVERY_STATE['last_warnings'] = []
            DISCOVERY_STATE['last_run_at'] = ''
            DISCOVERY_STATE['last_error'] = ''
            save_discovery_state()
            return export_discovery_state()

    def upsert_saved_discovery_query(query_payload: dict[str, object], *, last_run_at: str = '') -> None:
        clean = normalize_discovery_query(query_payload)
        if not clean:
            return
        if last_run_at:
            clean['last_run_at'] = normalize(last_run_at)
        with DISCOVERY_LOCK:
            existing = [item for item in DISCOVERY_STATE.get('saved_queries', []) if item.get('id') != clean['id']]
            existing.insert(0, clean)
            DISCOVERY_STATE['saved_queries'] = existing[:20]
            save_discovery_state()

    def delete_saved_discovery_query(query_id: str) -> dict[str, object]:
        clean_id = normalize(query_id)
        if not clean_id:
            raise ValueError('缺少搜索标识')
        with DISCOVERY_LOCK:
            DISCOVERY_STATE['saved_queries'] = [item for item in DISCOVERY_STATE.get('saved_queries', []) if item.get('id') != clean_id]
            save_discovery_state()
            return export_discovery_state()


    DISCOVERY_JOB_STAGE_LABELS = {
        'queued': '等待开始',
        'initial_search': '首轮搜索中',
        'initial_results': '首轮结果已返回',
        'seed_details': '正在补全详情',
        'expansion_search': '正在扩展相关词',
        'rescoring': '正在综合重排',
        'completed': '已完成',
        'failed': '执行失败',
        'cancelled': '已取消',
    }

    DISCOVERY_JOB_STAGE_PROGRESS = {
        'queued': 0.02,
        'initial_search': 0.16,
        'initial_results': 0.38,
        'seed_details': 0.52,
        'expansion_search': 0.74,
        'rescoring': 0.9,
        'completed': 1.0,
        'failed': 1.0,
        'cancelled': 1.0,
    }

    DISCOVERY_JOB_TERMINAL = {'completed', 'failed', 'cancelled'}

    def discovery_warning_list(items: object, *, limit: int = 8) -> list[str]:
        if not isinstance(items, list):
            return []
        return list(dict.fromkeys(normalize(item) for item in items if normalize(item)))[:limit]

    def empty_snapshot() -> dict[str, object]:
        snapshot = {'fetched_at': iso_now()}
        for period in PERIODS:
            snapshot[period['key']] = []
        return snapshot

    def load_snapshot() -> dict[str, object]:
        raw = load_json_file(LATEST_SNAPSHOT_PATH, empty_snapshot())
        if not isinstance(raw, dict):
            return empty_snapshot()
        snapshot = empty_snapshot()
        snapshot['fetched_at'] = normalize(raw.get('fetched_at')) or iso_now()
        for period in PERIODS:
            snapshot[period['key']] = [clean for repo in raw.get(period['key'], []) if (clean := normalize_repo(repo))]
            for repo in snapshot[period['key']]:
                apply_repo_translation(repo)
        return snapshot

    def save_snapshot(snapshot: dict[str, object]) -> None:
        atomic_write_json(LATEST_SNAPSHOT_PATH, snapshot)
    return SimpleNamespace(
        default_user_state=default_user_state,
        default_discovery_state=default_discovery_state,
        normalize_discovery_ranking_profile=normalize_discovery_ranking_profile,
        discovery_query_id=discovery_query_id,
        normalize_discovery_query=normalize_discovery_query,
        normalize_repo=normalize_repo,
        repo_from_url=repo_from_url,
        normalize_watch_entry=normalize_watch_entry,
        normalize_favorite_update=normalize_favorite_update,
        normalize_discovery_state=normalize_discovery_state,
        normalize_user_state=normalize_user_state,
        load_user_state=load_user_state,
        save_user_state=save_user_state,
        export_user_state=export_user_state,
        import_user_state=import_user_state,
        load_discovery_state=load_discovery_state,
        save_discovery_state=save_discovery_state,
        export_discovery_state=export_discovery_state,
        clear_discovery_results=clear_discovery_results,
        upsert_saved_discovery_query=upsert_saved_discovery_query,
        delete_saved_discovery_query=delete_saved_discovery_query,
        discovery_warning_list=discovery_warning_list,
        empty_snapshot=empty_snapshot,
        load_snapshot=load_snapshot,
        save_snapshot=save_snapshot,
        state_counts=state_counts,
        ordered_unique_urls=ordered_unique_urls,
        merge_favorite_updates=merge_favorite_updates,
    )
