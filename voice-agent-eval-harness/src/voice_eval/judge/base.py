"""Provider-neutral judge interface. Scoring logic never imports a provider SDK."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class JudgeRequest:
    transcript_id: str
    system_prompt: str
    user_prompt: str
    output_schema: dict[str, Any]
    max_tokens: int


@dataclass
class ProviderResponse:
    text: str
    model: str
    request_id: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)
    stop_reason: str | None = None


class ProviderError(Exception):
    """Base class for provider failures. Never converted into a score."""

    transient: bool = False


class TransientProviderError(ProviderError):
    """Retryable: rate limits, timeouts, connection errors, 5xx/overloaded."""

    transient = True

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class PermanentProviderError(ProviderError):
    """Not retryable: auth, bad request, refusal, missing credentials."""


class JudgeProvider(ABC):
    name: str = "abstract"
    is_llm: bool = True
    supports_structured_output: bool = False

    def __init__(self, model: str):
        self.model = model

    @abstractmethod
    def complete(self, request: JudgeRequest) -> ProviderResponse:
        """Return the raw model text for one transcript. Raise ProviderError on failure."""

    def describe(self) -> dict[str, Any]:
        return {
            "provider": self.name,
            "model": self.model,
            "is_llm": self.is_llm,
            "structured_output": self.supports_structured_output,
        }
