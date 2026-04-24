#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import logging
import threading
import time
from types import SimpleNamespace

from .redaction import SAFE_DISCOVERY_ERROR, redact_text

logger = logging.getLogger(__name__)

DISCOVERY_JOB_STAGE_LABELS = {
    "queued": "等待开始",
    "initial_search": "首轮搜索中",
    "initial_results": "首轮结果已返回",
    "seed_details": "正在补全详情",
    "expansion_search": "正在扩展相关词",
    "rescoring": "正在综合重排",
    "completed": "已完成",
    "failed": "执行失败",
    "cancelled": "已取消",
}

DISCOVERY_JOB_STAGE_PROGRESS = {
    "queued": 0.02,
    "initial_search": 0.16,
    "initial_results": 0.38,
    "seed_details": 0.52,
    "expansion_search": 0.74,
    "rescoring": 0.90,
    "completed": 1.0,
    "failed": 1.0,
    "cancelled": 1.0,
}

DISCOVERY_JOB_TERMINAL = {"completed", "failed", "cancelled"}


def make_discovery_job_runtime(
    *,
    settings: dict[str, object],
    normalize,
    clamp_int,
    as_bool,
    iso_now,
    normalize_repo,
    normalize_discovery_query,
    apply_discovery_result,
    discovery_warning_list,
    github_runtime,
    job_lock=None,
):
    discovery_jobs: dict[str, dict[str, object]] = {}
    active_job_id = ""
    runtime_lock = job_lock or threading.RLock()

    def estimate_discovery_eta(query_payload: dict[str, object]) -> tuple[int, int]:
        limit = clamp_int(query_payload.get("limit"), 20, 5, 100)
        has_token = bool(normalize(settings.get("github_token", "")))
        auto_expand = as_bool(query_payload.get("auto_expand"), True)
        size_penalty = max(0, (limit - 5) // 10) * 2
        initial_seconds = 14 + size_penalty
        if not has_token:
            initial_seconds += 2
        full_seconds = initial_seconds + (10 if auto_expand else 6) + (4 if has_token else 5) + size_penalty
        return initial_seconds, max(initial_seconds + 2, full_seconds)

    def build_discovery_job_message(
        stage: str,
        query_payload: dict[str, object],
        payload: dict[str, object] | None = None,
    ) -> str:
        query = normalize(query_payload.get("query")) or "当前关键词"
        payload = payload if isinstance(payload, dict) else {}
        result_count = len(payload.get("results", [])) if isinstance(payload.get("results"), list) else 0
        if stage == "initial_search":
            return f"正在围绕“{query}”执行首轮 GitHub 搜索"
        if stage == "initial_results":
            return f"首轮结果已返回 {result_count} 个候选，正在继续补全与扩词"
        if stage == "seed_details":
            return f"正在为“{query}”补全首批仓库详情"
        if stage == "expansion_search":
            return "正在扩展相关词并补充更多候选仓库"
        if stage == "rescoring":
            return f"正在对“{query}”执行综合打分与重排"
        if stage == "completed":
            return f"关键词发现已完成，共返回 {result_count} 个结果"
        if stage == "cancelled":
            return "关键词发现已取消"
        if stage == "failed":
            return SAFE_DISCOVERY_ERROR
        return "正在准备关键词发现任务"

    def build_discovery_job_snapshot(job: dict[str, object]) -> dict[str, object]:
        started_ts = float(job.get("_started_ts") or 0.0)
        finished_ts = float(job.get("_finished_ts") or 0.0)
        now_ts = finished_ts or time.time()
        elapsed_seconds = max(0, int(round(now_ts - started_ts))) if started_ts else 0
        eta_initial_seconds = clamp_int(job.get("eta_initial_seconds"), 4, 1, 300)
        eta_full_seconds = clamp_int(job.get("eta_full_seconds"), eta_initial_seconds + 2, eta_initial_seconds, 600)
        preview_results = [clean for item in job.get("preview_results", []) if (clean := normalize_repo(item))]
        status = normalize(job.get("status")) or "queued"
        target_seconds = eta_initial_seconds if not preview_results and status not in DISCOVERY_JOB_TERMINAL else eta_full_seconds
        eta_remaining_seconds = 0 if status in DISCOVERY_JOB_TERMINAL else max(1, target_seconds - elapsed_seconds)
        stage = normalize(job.get("stage")) or "queued"
        progress = max(0.0, min(1.0, float(job.get("progress") or 0.0)))
        return {
            "id": normalize(job.get("id")),
            "status": status,
            "stage": stage,
            "stage_label": normalize(job.get("stage_label")) or DISCOVERY_JOB_STAGE_LABELS.get(stage, "处理中"),
            "message": normalize(job.get("message")),
            "query": normalize_discovery_query(job.get("query")) or {},
            "save_query": as_bool(job.get("save_query"), False),
            "cancel_requested": as_bool(job.get("cancel_requested"), False),
            "created_at": normalize(job.get("created_at")),
            "started_at": normalize(job.get("started_at")),
            "finished_at": normalize(job.get("finished_at")),
            "elapsed_seconds": elapsed_seconds,
            "eta_initial_seconds": eta_initial_seconds,
            "eta_full_seconds": eta_full_seconds,
            "eta_remaining_seconds": eta_remaining_seconds,
            "progress": progress,
            "progress_percent": max(0, min(100, int(round(progress * 100)))),
            "translated_query": normalize(job.get("translated_query")),
            "generated_queries": [normalize(item) for item in job.get("generated_queries", []) if normalize(item)][:12]
            if isinstance(job.get("generated_queries"), list)
            else [],
            "related_terms": [normalize(item) for item in job.get("related_terms", []) if normalize(item)][:12]
            if isinstance(job.get("related_terms"), list)
            else [],
            "warnings": discovery_warning_list(job.get("warnings"), limit=8),
            "preview_results": preview_results[:100],
            "error": normalize(job.get("error")),
            "discovery_state": job.get("discovery_state") if isinstance(job.get("discovery_state"), dict) else None,
        }

    def prune_terminal_jobs() -> None:
        stale_ids = [
            key
            for key, value in discovery_jobs.items()
            if key != active_job_id and normalize(value.get("status")) in DISCOVERY_JOB_TERMINAL
        ]
        for stale_id in stale_ids[:-10]:
            discovery_jobs.pop(stale_id, None)

    def export_active_discovery_job() -> dict[str, object] | None:
        with runtime_lock:
            job = discovery_jobs.get(active_job_id) if active_job_id else None
            if not isinstance(job, dict):
                return None
            return build_discovery_job_snapshot(job)

    def update_discovery_job(job_id: str, **changes) -> dict[str, object] | None:
        nonlocal active_job_id
        clean_id = normalize(job_id)
        if not clean_id:
            return None
        with runtime_lock:
            job = discovery_jobs.get(clean_id)
            if not isinstance(job, dict):
                return None
            if "status" in changes and normalize(changes.get("status")) == "running" and not normalize(job.get("started_at")):
                job["started_at"] = iso_now()
                job["_started_ts"] = time.time()
            if "stage" in changes:
                stage = normalize(changes.get("stage")) or normalize(job.get("stage")) or "queued"
                job["stage"] = stage
                job["stage_label"] = DISCOVERY_JOB_STAGE_LABELS.get(stage, stage)
                job["progress"] = DISCOVERY_JOB_STAGE_PROGRESS.get(stage, job.get("progress", 0.0))
            for key in ("status", "message", "translated_query", "error"):
                if key in changes and changes.get(key) is not None:
                    job[key] = normalize(changes.get(key))
            for key in ("generated_queries", "related_terms"):
                if key in changes and changes.get(key) is not None:
                    job[key] = [normalize(item) for item in changes.get(key, []) if normalize(item)][:12]
            if "warnings" in changes and changes.get("warnings") is not None:
                existing = discovery_warning_list(job.get("warnings"), limit=8)
                incoming = discovery_warning_list(changes.get("warnings"), limit=8)
                job["warnings"] = list(dict.fromkeys([*existing, *incoming]))[:8]
            if "preview_results" in changes and changes.get("preview_results") is not None:
                job["preview_results"] = [clean for item in changes.get("preview_results", []) if (clean := normalize_repo(item))][:100]
            if "discovery_state" in changes and isinstance(changes.get("discovery_state"), dict):
                job["discovery_state"] = changes.get("discovery_state")
            if "cancel_requested" in changes:
                job["cancel_requested"] = as_bool(changes.get("cancel_requested"), False)
            status = normalize(job.get("status")) or "queued"
            if status in DISCOVERY_JOB_TERMINAL:
                job["finished_at"] = normalize(job.get("finished_at")) or iso_now()
                job["_finished_ts"] = float(job.get("_finished_ts") or time.time())
                if active_job_id == clean_id:
                    active_job_id = ""
            else:
                active_job_id = clean_id
            snapshot = build_discovery_job_snapshot(job)
            prune_terminal_jobs()
            return snapshot

    def run_discovery_search(payload: object) -> dict[str, object]:
        query_payload = normalize_discovery_query(payload)
        if not query_payload:
            raise ValueError("请输入关键词")
        save_query = as_bool(payload.get("save_query") if isinstance(payload, dict) else False, False)
        discovery = github_runtime.discover_repos(
            query=query_payload["query"],
            limit=query_payload["limit"],
            auto_expand=query_payload["auto_expand"],
            ranking_profile=query_payload["ranking_profile"],
        )
        return apply_discovery_result(query_payload, discovery, save_query=save_query)

    def start_discovery_job(payload: object) -> dict[str, object]:
        nonlocal active_job_id
        query_payload = normalize_discovery_query(payload)
        if not query_payload:
            raise ValueError("请输入关键词")
        save_query = as_bool(payload.get("save_query") if isinstance(payload, dict) else False, False)
        eta_initial_seconds, eta_full_seconds = estimate_discovery_eta(query_payload)
        job_hash = hashlib.sha1(f"{query_payload['id']}-{time.time()}".encode("utf-8")).hexdigest()[:8]
        job_id = f"discover-{int(time.time() * 1000)}-{job_hash}"
        created_at = iso_now()
        with runtime_lock:
            for other_id, other in discovery_jobs.items():
                if other_id == job_id:
                    continue
                if normalize(other.get("status")) not in DISCOVERY_JOB_TERMINAL:
                    other["cancel_requested"] = True
                    other["message"] = "已有新的关键词发现开始，当前任务正在取消"
            discovery_jobs[job_id] = {
                "id": job_id,
                "status": "queued",
                "stage": "queued",
                "stage_label": DISCOVERY_JOB_STAGE_LABELS["queued"],
                "message": "正在准备关键词发现任务",
                "query": query_payload,
                "save_query": save_query,
                "cancel_requested": False,
                "created_at": created_at,
                "started_at": "",
                "finished_at": "",
                "progress": DISCOVERY_JOB_STAGE_PROGRESS["queued"],
                "eta_initial_seconds": eta_initial_seconds,
                "eta_full_seconds": eta_full_seconds,
                "translated_query": "",
                "generated_queries": [],
                "related_terms": [],
                "warnings": [],
                "preview_results": [],
                "error": "",
                "discovery_state": None,
                "_created_ts": time.time(),
                "_started_ts": 0.0,
                "_finished_ts": 0.0,
            }
            active_job_id = job_id
            snapshot = build_discovery_job_snapshot(discovery_jobs[job_id])

        cancel_error = getattr(github_runtime, "DiscoveryCancelledError", RuntimeError)
        started_ts = time.perf_counter()

        def worker() -> None:
            def is_cancelled() -> bool:
                with runtime_lock:
                    job = discovery_jobs.get(job_id, {})
                    return as_bool(job.get("cancel_requested"), False)

            def on_progress(stage: str, progress_payload: dict[str, object]) -> None:
                update_discovery_job(
                    job_id,
                    status="running",
                    stage=stage,
                    message=build_discovery_job_message(stage, query_payload, progress_payload),
                    translated_query=progress_payload.get("translated_query"),
                    generated_queries=progress_payload.get("generated_queries"),
                    related_terms=progress_payload.get("related_terms"),
                    warnings=progress_payload.get("warnings"),
                    preview_results=progress_payload.get("results"),
                )

            try:
                update_discovery_job(
                    job_id,
                    status="running",
                    stage="initial_search",
                    message=build_discovery_job_message("initial_search", query_payload),
                )
                discovery = github_runtime.discover_repos(
                    query=query_payload["query"],
                    limit=query_payload["limit"],
                    auto_expand=query_payload["auto_expand"],
                    ranking_profile=query_payload["ranking_profile"],
                    progress_callback=on_progress,
                    is_cancelled=is_cancelled,
                )
                if is_cancelled():
                    raise cancel_error("关键词发现已取消")
                discovery_state = apply_discovery_result(query_payload, discovery, save_query=save_query)
                update_discovery_job(
                    job_id,
                    status="completed",
                    stage="completed",
                    message=build_discovery_job_message(
                        "completed",
                        query_payload,
                        {"results": discovery_state.get("last_results", [])},
                    ),
                    translated_query=discovery.get("translated_query"),
                    generated_queries=discovery.get("generated_queries"),
                    related_terms=discovery.get("related_terms"),
                    warnings=discovery.get("warnings"),
                    preview_results=discovery_state.get("last_results"),
                    discovery_state=discovery_state,
                )
                logger.info(
                    "discovery_job_completed job_id=%s query=%r result_count=%d duration_ms=%d",
                    job_id,
                    query_payload["query"],
                    len(discovery_state.get("last_results", [])),
                    int((time.perf_counter() - started_ts) * 1000),
                )
            except cancel_error:
                update_discovery_job(
                    job_id,
                    status="cancelled",
                    stage="cancelled",
                    message=build_discovery_job_message("cancelled", query_payload),
                )
                logger.info(
                    "discovery_job_cancelled job_id=%s query=%r duration_ms=%d",
                    job_id,
                    query_payload["query"],
                    int((time.perf_counter() - started_ts) * 1000),
                )
            except Exception as exc:
                update_discovery_job(
                    job_id,
                    status="failed",
                    stage="failed",
                    message=build_discovery_job_message("failed", query_payload, {"error": SAFE_DISCOVERY_ERROR}),
                    error=SAFE_DISCOVERY_ERROR,
                )
                logger.warning(
                    "discovery_job_failed job_id=%s query=%r duration_ms=%d error=%s",
                    job_id,
                    query_payload["query"],
                    int((time.perf_counter() - started_ts) * 1000),
                    redact_text(exc),
                )

        threading.Thread(target=worker, name=f"discovery-job-{job_id}", daemon=True).start()
        return snapshot

    def get_discovery_job(job_id: str) -> dict[str, object]:
        clean_id = normalize(job_id)
        if not clean_id:
            active = export_active_discovery_job()
            if active:
                return active
            raise ValueError("缺少关键词发现任务标识")
        with runtime_lock:
            job = discovery_jobs.get(clean_id)
            if not isinstance(job, dict):
                raise ValueError("未找到对应的关键词发现任务")
            return build_discovery_job_snapshot(job)

    def cancel_discovery_job(job_id: str) -> dict[str, object]:
        clean_id = normalize(job_id)
        if not clean_id:
            raise ValueError("缺少关键词发现任务标识")
        with runtime_lock:
            job = discovery_jobs.get(clean_id)
            if not isinstance(job, dict):
                raise ValueError("未找到对应的关键词发现任务")
            status = normalize(job.get("status"))
            if status in DISCOVERY_JOB_TERMINAL:
                return build_discovery_job_snapshot(job)
            job["cancel_requested"] = True
            job["message"] = "已收到取消请求，当前阶段结束后会停止"
            return build_discovery_job_snapshot(job)

    return SimpleNamespace(
        estimate_discovery_eta=estimate_discovery_eta,
        export_active_discovery_job=export_active_discovery_job,
        update_discovery_job=update_discovery_job,
        run_discovery_search=run_discovery_search,
        start_discovery_job=start_discovery_job,
        get_discovery_job=get_discovery_job,
        cancel_discovery_job=cancel_discovery_job,
        build_discovery_job_snapshot=build_discovery_job_snapshot,
        build_discovery_job_message=build_discovery_job_message,
    )
