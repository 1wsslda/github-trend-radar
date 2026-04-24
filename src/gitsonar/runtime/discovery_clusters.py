#!/usr/bin/env python3
from __future__ import annotations

"""Local, dependency-free clustering for discovery result lists."""

import re
from collections import Counter, defaultdict

TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9+#._-]*|[\u4e00-\u9fff]{2,}", re.IGNORECASE)

STOP_TERMS = {
    "a",
    "an",
    "and",
    "api",
    "app",
    "awesome",
    "demo",
    "for",
    "github",
    "helper",
    "helpers",
    "library",
    "open",
    "project",
    "repo",
    "sample",
    "sdk",
    "source",
    "the",
    "tool",
    "tools",
    "toolkit",
    "with",
}

ACRONYM_LABELS = {
    "ai": "AI",
    "api": "API",
    "cli": "CLI",
    "db": "DB",
    "gui": "GUI",
    "llm": "LLM",
    "rpa": "RPA",
    "sdk": "SDK",
    "ui": "UI",
}


def _clean_term(value: object, normalize) -> str:
    clean = normalize(value).lower().replace("_", " ").replace("-", " ").replace(".", " ").replace("/", " ")
    return " ".join(part for part in clean.split() if part)


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:48] or "other"


def _label(value: str) -> str:
    parts = value.split()
    if not parts:
        return "Other"
    return " ".join(ACRONYM_LABELS.get(part, part.capitalize()) for part in parts)


def _tokenize(value: object, normalize) -> list[str]:
    clean = normalize(value).lower()
    terms: list[str] = []
    for token in TOKEN_RE.findall(clean):
        normalized = _clean_term(token, normalize)
        if not normalized or normalized in STOP_TERMS or normalized.isdigit() or len(normalized) < 2:
            continue
        terms.append(normalized)
    return list(dict.fromkeys(terms))


def _repo_terms(repo: dict[str, object], normalize) -> Counter[str]:
    terms: Counter[str] = Counter()
    topics = repo.get("topics", []) if isinstance(repo.get("topics"), list) else []
    for topic in topics:
        phrase = _clean_term(topic, normalize)
        if phrase and phrase not in STOP_TERMS:
            terms[phrase] += 8
        for token in _tokenize(topic, normalize):
            terms[token] += 3
    for term in repo.get("matched_terms", []) if isinstance(repo.get("matched_terms"), list) else []:
        clean = _clean_term(term, normalize)
        if clean and clean not in STOP_TERMS:
            terms[clean] += 6
    full_name = normalize(repo.get("full_name"))
    name = full_name.split("/", 1)[1] if "/" in full_name else full_name
    for token in _tokenize(name, normalize):
        terms[token] += 4
    for field in ("description", "description_raw", "language"):
        for token in _tokenize(repo.get(field), normalize):
            terms[token] += 1
    return terms


def _choose_anchor(terms: Counter[str], document_frequency: Counter[str]) -> str:
    if not terms:
        return ""
    return max(
        terms,
        key=lambda term: (
            20 if document_frequency[term] >= 2 and len(term.split()) >= 2 else 0,
            terms[term] + document_frequency[term] * 2,
            len(term.split()),
            document_frequency[term],
            term,
        ),
    )


def cluster_discovery_results(
    repos: object,
    *,
    normalize,
    max_clusters: int = 12,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    clean_repos = [dict(item) for item in repos if isinstance(item, dict)] if isinstance(repos, list) else []
    if not clean_repos:
        return [], []

    repo_terms = [_repo_terms(repo, normalize) for repo in clean_repos]
    document_frequency: Counter[str] = Counter()
    for terms in repo_terms:
        document_frequency.update(terms.keys())

    assignments: list[str] = []
    for repo, terms in zip(clean_repos, repo_terms):
        anchor = _choose_anchor(terms, document_frequency)
        if not anchor:
            anchor = _clean_term(repo.get("language"), normalize) or "other"
        assignments.append(anchor)

    cluster_order = list(dict.fromkeys(assignments))[:max_clusters]
    cluster_ids = {anchor: f"cluster-{_slug(anchor)}" for anchor in cluster_order}
    fallback_id = "cluster-other"

    annotated: list[dict[str, object]] = []
    cluster_items: dict[str, list[dict[str, object]]] = defaultdict(list)
    cluster_term_counts: dict[str, Counter[str]] = defaultdict(Counter)
    cluster_languages: dict[str, list[str]] = defaultdict(list)

    for repo, anchor, terms in zip(clean_repos, assignments, repo_terms):
        if anchor not in cluster_ids:
            anchor = "other"
        cluster_id = cluster_ids.get(anchor, fallback_id)
        cluster_label = _label(anchor)
        item = dict(repo)
        item["cluster_id"] = cluster_id
        item["cluster_label"] = cluster_label
        annotated.append(item)
        cluster_items[cluster_id].append(item)
        cluster_term_counts[cluster_id].update(terms)
        language = normalize(repo.get("language"))
        if language and language not in cluster_languages[cluster_id]:
            cluster_languages[cluster_id].append(language)

    clusters: list[dict[str, object]] = []
    anchor_by_id = {cluster_ids[anchor]: anchor for anchor in cluster_ids}
    for cluster_id, items in cluster_items.items():
        anchor = anchor_by_id.get(cluster_id, "other")
        repo_urls = [normalize(item.get("url")) for item in items if normalize(item.get("url"))]
        average_score = sum(int(item.get("composite_score") or 0) for item in items) / max(1, len(items))
        clusters.append(
            {
                "id": cluster_id,
                "label": _label(anchor),
                "count": len(items),
                "repo_urls": repo_urls[:100],
                "top_terms": [term for term, _count in cluster_term_counts[cluster_id].most_common(6)],
                "languages": cluster_languages[cluster_id][:6],
                "_average_score": average_score,
            }
        )

    clusters.sort(key=lambda item: (-int(item.get("count") or 0), -float(item.get("_average_score") or 0.0), str(item.get("label") or "")))
    for cluster in clusters:
        cluster.pop("_average_score", None)
    return annotated, clusters


__all__ = ["cluster_discovery_results"]
