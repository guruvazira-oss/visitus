"""Concrete judge providers and the retry / rate-limit wrapper.

Provider-specific code lives only here. Switching providers means adding one class and a
branch in ``get_provider``; the scoring pipeline is unchanged.
"""

from __future__ import annotations

import contextlib
import os
import random
import threading
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

from voice_eval.config import JudgeSettings, load_settings
from voice_eval.judge.base import (
    JudgeProvider,
    JudgeRequest,
    PermanentProviderError,
    ProviderError,
    ProviderResponse,
    TransientProviderError,
)


class AnthropicProvider(JudgeProvider):
    """Claude via the official Anthropic SDK with schema-constrained JSON output."""

    name = "anthropic"
    is_llm = True
    supports_structured_output = True

    def __init__(self, settings: JudgeSettings, client: Any | None = None):
        super().__init__(settings.model)
        self.settings = settings
        self._client = client
        self.refusal_fallback = bool(
            load_settings().get("judge", {}).get("refusal_fallback", False)
        )

    def _get_client(self) -> Any:
        if self._client is None:
            import anthropic  # imported lazily: never needed for offline use

            key = os.environ.get(self.settings.api_key_env)
            if not key:
                raise PermanentProviderError(
                    f"{self.settings.api_key_env} is not set. Configure it in .env to run a live "
                    "evaluation, or use --provider heuristic for the offline baseline."
                )
            # SDK retries disabled: our wrapper retries so attempts are counted and logged.
            self._client = anthropic.Anthropic(
                api_key=key, max_retries=0, timeout=self.settings.timeout_seconds
            )
        return self._client

    def complete(self, request: JudgeRequest) -> ProviderResponse:
        import anthropic

        client = self._get_client()
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": request.max_tokens,
            "system": request.system_prompt,
            "messages": [{"role": "user", "content": request.user_prompt}],
            "output_config": {
                "format": {"type": "json_schema", "schema": request.output_schema},
                "effort": self.settings.effort,
            },
        }
        try:
            if self.refusal_fallback:
                resp = client.beta.messages.create(
                    betas=["server-side-fallback-2026-07-01"], fallbacks="default", **kwargs
                )
            else:
                resp = client.messages.create(**kwargs)
        except anthropic.RateLimitError as exc:
            retry_after = None
            with contextlib.suppress(TypeError, ValueError, AttributeError):
                retry_after = float(exc.response.headers.get("retry-after", ""))
            raise TransientProviderError(f"rate limited: {exc.message}", retry_after) from exc
        except (anthropic.APITimeoutError, anthropic.APIConnectionError) as exc:
            raise TransientProviderError(f"{type(exc).__name__}: {exc}") from exc
        except anthropic.APIStatusError as exc:
            if exc.status_code >= 500 or exc.status_code in (408, 409):
                raise TransientProviderError(f"HTTP {exc.status_code}: {exc.message}") from exc
            raise PermanentProviderError(f"HTTP {exc.status_code}: {exc.message}") from exc

        if resp.stop_reason == "refusal":
            raise PermanentProviderError(
                "model refused to evaluate this transcript (stop_reason=refusal)"
            )
        if resp.stop_reason == "max_tokens":
            raise TransientProviderError("response truncated at max_tokens")
        text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
        usage = {}
        if getattr(resp, "usage", None) is not None:
            usage = {
                "input_tokens": resp.usage.input_tokens,
                "output_tokens": resp.usage.output_tokens,
            }
        return ProviderResponse(
            text=text,
            model=resp.model,
            request_id=getattr(resp, "_request_id", None),
            usage=usage,
            stop_reason=resp.stop_reason,
        )


class HeuristicProvider(JudgeProvider):
    """Offline rule-based baseline. NOT an LLM; labelled as such in every artifact."""

    name = "heuristic"
    is_llm = False
    supports_structured_output = True

    def __init__(self, rubric_rules: dict[str, Any] | None = None):
        from voice_eval.judge.heuristic import HEURISTIC_MODEL_ID

        super().__init__(HEURISTIC_MODEL_ID)
        self.rubric_rules = rubric_rules or {}
        self._transcripts: dict[str, Any] = {}

    def register(self, transcripts: Iterable[Any]) -> None:
        self._transcripts.update({t.transcript_id: t for t in transcripts})

    def complete(self, request: JudgeRequest) -> ProviderResponse:
        from voice_eval.judge.heuristic import heuristic_judge_json

        t = self._transcripts.get(request.transcript_id)
        if t is None:
            raise PermanentProviderError(
                f"transcript {request.transcript_id} not registered with heuristic provider"
            )
        return ProviderResponse(text=heuristic_judge_json(t, self.rubric_rules), model=self.model)


class MockProvider(JudgeProvider):
    """Scripted provider for tests. Each script item is a str (raw text), a dict (JSON-encoded),
    an Exception instance (raised), or a callable(request) -> any of those."""

    name = "mock"
    is_llm = False
    supports_structured_output = False

    def __init__(
        self, script: list[Any] | Callable[[JudgeRequest], Any], model: str = "mock-judge"
    ):
        super().__init__(model)
        self.script = script
        self.calls: list[JudgeRequest] = []

    def complete(self, request: JudgeRequest) -> ProviderResponse:
        import json

        self.calls.append(request)
        item = self.script(request) if callable(self.script) else self.script.pop(0)
        if callable(item):
            item = item(request)
        if isinstance(item, Exception):
            raise item
        text = item if isinstance(item, str) else json.dumps(item)
        return ProviderResponse(text=text, model=self.model)


def get_provider(
    name: str, settings: JudgeSettings, rubric_rules: dict[str, Any] | None = None
) -> JudgeProvider:
    if name == "anthropic":
        return AnthropicProvider(settings)
    if name == "heuristic":
        return HeuristicProvider(rubric_rules)
    raise ValueError(
        f"unknown provider {name!r}; expected 'anthropic' or 'heuristic' (mock is test-only)"
    )


@dataclass
class RetryOutcome:
    response: ProviderResponse | None
    attempts: int
    error: ProviderError | None


class RateLimiter:
    """Minimum spacing between requests (client-side politeness, on top of retry-after)."""

    def __init__(
        self,
        min_interval: float,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.min_interval = min_interval
        self.clock, self.sleep = clock, sleep
        self._last = -1e18
        self._lock = threading.Lock()

    def wait(self) -> None:
        with self._lock:
            delay = self._last + self.min_interval - self.clock()
            if delay > 0:
                self.sleep(delay)
            self._last = self.clock()


def call_with_retries(
    provider: JudgeProvider,
    request: JudgeRequest,
    max_retries: int,
    limiter: RateLimiter | None = None,
    sleep: Callable[[float], None] = time.sleep,
    base_delay: float = 2.0,
    max_delay: float = 60.0,
) -> RetryOutcome:
    """Exponential backoff with jitter on transient errors; permanent errors fail fast."""
    attempts = 0
    while True:
        attempts += 1
        if limiter:
            limiter.wait()
        try:
            return RetryOutcome(provider.complete(request), attempts, None)
        except ProviderError as exc:
            if not exc.transient or attempts > max_retries:
                return RetryOutcome(None, attempts, exc)
            delay = getattr(exc, "retry_after", None) or min(
                max_delay, base_delay * 2 ** (attempts - 1)
            )
            sleep(delay + random.uniform(0, 0.25 * delay))
