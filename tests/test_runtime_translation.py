from __future__ import annotations

import re
import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import gitsonar.runtime.translation as translation_module
from gitsonar.runtime.translation import make_translation_runtime
from gitsonar.runtime.utils import normalize


class _DummyResponse:
    def __init__(self, translated: str):
        self._translated = translated

    def raise_for_status(self) -> None:
        return None

    def json(self) -> list[object]:
        return [[[self._translated]]]


class _DummyChatResponse:
    def __init__(self, translated: str):
        self._translated = translated

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return {"choices": [{"message": {"content": self._translated}}]}


class _DummySession:
    def __init__(self, responses: list[object] | None = None):
        self.responses = list(responses or [])
        self.calls: list[dict[str, object]] = []
        self.post_calls: list[dict[str, object]] = []

    def get(self, url: str, *, params: dict[str, object], timeout: object) -> object:
        self.calls.append({"url": url, "params": dict(params), "timeout": timeout})
        if not self.responses:
            raise AssertionError("unexpected translation request")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    def post(self, url: str, *, json: dict[str, object], timeout: object, **kwargs) -> object:
        self.post_calls.append({"url": url, "json": dict(json), "timeout": timeout, "kwargs": dict(kwargs)})
        if not self.responses:
            raise AssertionError("unexpected local translation request")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class _ImmediateFuture:
    def __init__(self, *, result: object = None, error: BaseException | None = None):
        self._result = result
        self._error = error

    def result(self) -> object:
        if self._error is not None:
            raise self._error
        return self._result


class _ImmediateExecutor:
    def __init__(self, max_workers: int):
        self.max_workers = max_workers

    def __enter__(self) -> "_ImmediateExecutor":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def submit(self, fn, *args, **kwargs) -> _ImmediateFuture:
        try:
            return _ImmediateFuture(result=fn(*args, **kwargs))
        except BaseException as exc:  # pragma: no cover - defensive passthrough
            return _ImmediateFuture(error=exc)


def build_translation_runtime(
    *,
    cache: dict[str, str] | None = None,
    responses: list[object] | None = None,
    writes: list[tuple[str, dict[str, str]]] | None = None,
    settings: dict[str, object] | None = None,
):
    cache_store = dict(cache or {})
    write_log = writes if writes is not None else []
    session = _DummySession(responses)
    runtime = make_translation_runtime(
        cache_path=str(ROOT / "artifacts" / "_translation_cache.json"),
        translation_cache=cache_store,
        translation_lock=threading.RLock(),
        translate_session=session,
        settings=settings or {},
        normalize=normalize,
        load_json_file=lambda _path, default: default,
        atomic_write_json=lambda path, payload: write_log.append((str(path), dict(payload))),
        translate_timeout=(1, 2),
        translate_retries=2,
        max_translation_cache_size=10,
        han_re=re.compile(r"[\u3400-\u9fff]"),
        thread_pool_executor_cls=_ImmediateExecutor,
        as_completed=lambda futures: list(futures),
        periods=[{"key": "daily", "label": "Today", "days": 1}],
    )
    return runtime, cache_store, session, write_log


class RuntimeTranslationTests(unittest.TestCase):
    def test_translate_text_uses_cached_value_without_request(self):
        runtime, _cache_store, session, _writes = build_translation_runtime(cache={"fast cli": "快速工具"})

        translated = runtime.translate_text("fast cli")

        self.assertEqual(translated, "快速工具")
        self.assertEqual(session.calls, [])

    def test_translate_text_retries_then_falls_back_to_original(self):
        runtime, _cache_store, session, _writes = build_translation_runtime(
            responses=[RuntimeError("boom"), RuntimeError("still boom")]
        )

        with patch.object(translation_module.time, "sleep", lambda _seconds: None):
            translated = runtime.translate_text("fast cli")

        self.assertEqual(translated, "fast cli")
        self.assertEqual(len(session.calls), 2)

    def test_translate_text_short_circuits_han_input(self):
        runtime, _cache_store, session, _writes = build_translation_runtime()

        translated = runtime.translate_text("已经是中文")

        self.assertEqual(translated, "已经是中文")
        self.assertEqual(session.calls, [])

    def test_translate_query_to_en_short_circuits_non_han_input(self):
        runtime, _cache_store, session, _writes = build_translation_runtime()

        translated = runtime.translate_query_to_en("open source cli")

        self.assertEqual(translated, "open source cli")
        self.assertEqual(session.calls, [])

    def test_translate_query_to_en_caches_han_queries_with_en_prefix(self):
        runtime, cache_store, session, _writes = build_translation_runtime(responses=[_DummyResponse("open source")])

        translated = runtime.translate_query_to_en("开源")

        self.assertEqual(translated, "open source")
        self.assertEqual(cache_store["en::开源"], "open source")
        self.assertEqual(session.calls[0]["params"]["tl"], "en")

    def test_openai_compatible_provider_posts_chat_completion_when_configured(self):
        runtime, cache_store, session, _writes = build_translation_runtime(
            responses=[_DummyChatResponse("快速命令行工具")],
            settings={
                "translation_provider": "openai_compatible",
                "translation_api_endpoint": "https://api.example.test/v1/chat/completions",
                "translation_api_model": "gpt-4o-mini",
                "translation_api_key": "test-key",
            },
        )

        translated = runtime.translate_text("fast cli tool")

        self.assertEqual(translated, "快速命令行工具")
        self.assertEqual(session.calls, [])
        self.assertEqual(session.post_calls[0]["url"], "https://api.example.test/v1/chat/completions")
        self.assertEqual(session.post_calls[0]["json"]["model"], "gpt-4o-mini")
        self.assertEqual(session.post_calls[0]["json"]["temperature"], 0)
        self.assertFalse(session.post_calls[0]["json"]["stream"])
        self.assertEqual(
            session.post_calls[0]["json"]["messages"],
            [
                {
                    "role": "system",
                    "content": "Translate text. Return only the translated text, with no explanation or quotes.",
                },
                {
                    "role": "user",
                    "content": "Translate the following text to Simplified Chinese:\n\nfast cli tool",
                },
            ],
        )
        self.assertEqual(session.post_calls[0]["kwargs"]["headers"]["Authorization"], "Bearer test-key")
        self.assertNotIn("test-key", next(iter(cache_store)))
        self.assertEqual(
            cache_store[
                "openai_compatible::https://api.example.test/v1/chat/completions::gpt-4o-mini::zh-CN::fast cli tool"
            ],
            "快速命令行工具",
        )

    def test_openai_compatible_provider_requires_key_and_model_and_never_falls_back_to_google(self):
        runtime, cache_store, session, _writes = build_translation_runtime(
            responses=[_DummyResponse("should not be used")],
            settings={
                "translation_provider": "openai_compatible",
                "translation_api_endpoint": "https://api.example.test/v1/chat/completions",
                "translation_api_model": "",
                "translation_api_key": "test-key",
            },
        )

        translated = runtime.translate_text("fast cli tool")

        self.assertEqual(translated, "fast cli tool")
        self.assertEqual(cache_store, {})
        self.assertEqual(session.calls, [])
        self.assertEqual(session.post_calls, [])

    def test_openai_compatible_provider_empty_response_returns_original_without_google_fallback(self):
        runtime, cache_store, session, _writes = build_translation_runtime(
            responses=[_DummyChatResponse("")],
            settings={
                "translation_provider": "openai_compatible",
                "translation_api_endpoint": "https://api.example.test/v1/chat/completions",
                "translation_api_model": "gpt-4o-mini",
                "translation_api_key": "test-key",
            },
        )

        translated = runtime.translate_text("fast cli tool")

        self.assertEqual(translated, "fast cli tool")
        self.assertEqual(cache_store, {})
        self.assertEqual(session.calls, [])
        self.assertEqual(len(session.post_calls), 1)

    def test_translate_snapshot_flushes_cache_after_batch_translation(self):
        runtime, _cache_store, session, writes = build_translation_runtime(
            responses=[_DummyResponse("快速工具"), _DummyResponse("文档站点")]
        )
        snapshot = {
            "daily": [
                {"full_name": "octo/cli", "url": "https://github.com/octo/cli", "description": "fast cli"},
                {"full_name": "octo/docs", "url": "https://github.com/octo/docs", "description": "docs site"},
            ]
        }

        runtime.translate_snapshot(snapshot)

        self.assertEqual(snapshot["daily"][0]["description"], "快速工具")
        self.assertEqual(snapshot["daily"][1]["description"], "文档站点")
        self.assertEqual(len(session.calls), 2)
        self.assertEqual(len(writes), 1)
        self.assertEqual(writes[0][1]["fast cli"], "快速工具")
        self.assertEqual(writes[0][1]["docs site"], "文档站点")
        self.assertFalse(runtime.flush_translation_cache())


if __name__ == "__main__":
    unittest.main()
