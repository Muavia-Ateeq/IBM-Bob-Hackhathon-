from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any, Protocol, Sequence

from app.config import Settings


class ProviderUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class Completion:
    payload: dict[str, Any]
    input_tokens: int = 0
    output_tokens: int = 0


class Provider(Protocol):
    model_id: str

    async def complete_json(self, system: str, user: str, schema: dict[str, Any]) -> Completion: ...


class UnavailableProvider:
    model_id = "unavailable"

    def __init__(self, reason: str) -> None:
        self._reason = reason

    @property
    def reason(self) -> str:
        return self._reason

    async def complete_json(self, system: str, user: str, schema: dict[str, Any]) -> Completion:
        raise ProviderUnavailable(self._reason)


class StaticProvider:
    """Deterministic provider for tests. Returns a fixed payload; never touches the network."""

    def __init__(self, payload: dict[str, Any], model_id: str = "static-test") -> None:
        self._payload = payload
        self.model_id = model_id
        self.calls = 0

    async def complete_json(self, system: str, user: str, schema: dict[str, Any]) -> Completion:
        self.calls += 1
        return Completion(payload=self._payload, input_tokens=0, output_tokens=0)


class GroqProvider:
    """Groq Structured Outputs in strict mode.

    Verified constraints, from console.groq.com/docs/structured-outputs:
    strict mode requires every field to be required and additionalProperties false.
    Streaming and tool use are not supported alongside Structured Outputs.
    """

    def __init__(self, api_key: str, model_id: str) -> None:
        from groq import AsyncGroq

        self._client = AsyncGroq(api_key=api_key)
        self.model_id = model_id

    async def complete_json(self, system: str, user: str, schema: dict[str, Any]) -> Completion:
        response = await self._client.chat.completions.create(
            model=self.model_id,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "trustgate_findings",
                    "strict": True,
                    "schema": schema,
                },
            },
            temperature=0,
        )
        content = response.choices[0].message.content or "{}"
        usage = getattr(response, "usage", None)
        return Completion(
            payload=json.loads(content),
            input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            output_tokens=getattr(usage, "completion_tokens", 0) or 0,
        )


class FallbackProvider:
    """An ordered chain. The first provider that answers serves the request; the rest are
    only reached if it fails.

    Every failure is recorded and printed once to stderr, naming the provider and the reason.
    If every provider fails, `ProviderUnavailable` is raised carrying all of their reasons —
    the point of a fallback chain is that the failure is visible, not that it is hidden behind
    whichever provider happened to be last.

    `model_id` is the provider that actually served the last request, not the first one tried.
    """

    def __init__(self, providers: Sequence[Provider]) -> None:
        self._providers = tuple(providers)
        self._served_by: Provider | None = None
        self.failures: list[str] = []

    @property
    def model_id(self) -> str:
        if self._served_by is None:
            return "unresolved"
        return self._served_by.model_id

    @property
    def providers(self) -> tuple[Provider, ...]:
        return self._providers

    async def complete_json(self, system: str, user: str, schema: dict[str, Any]) -> Completion:
        if not self._providers:
            raise ProviderUnavailable("no LLM provider is configured")

        self.failures = []
        for provider in self._providers:
            try:
                completion = await provider.complete_json(system, user, schema)
            except Exception as exc:
                reason = f"{provider.model_id}: {type(exc).__name__}: {exc}"
                self.failures.append(reason)
                print(f"provider unavailable, trying the next one — {reason}", file=sys.stderr)
                continue
            self._served_by = provider
            return completion

        raise ProviderUnavailable(
            "every configured LLM provider failed — " + "; ".join(self.failures)
        )


def build_provider(settings: Settings) -> Provider:
    """IBM watsonx.ai first, Groq second. Order is the product decision, not a default."""
    from app.llm.watsonx_client import WatsonxProvider

    chain: list[Provider] = []

    if settings.watsonx_api_key:
        try:
            chain.append(
                WatsonxProvider(
                    api_key=settings.watsonx_api_key,
                    model_id=settings.watsonx_model_id,
                    url=settings.watsonx_url,
                    project_id=settings.watsonx_project_id,
                    space_id=settings.watsonx_space_id,
                )
            )
        except ProviderUnavailable as exc:
            print(f"watsonx.ai is not usable: {exc}", file=sys.stderr)

    if settings.groq_api_key:
        chain.append(GroqProvider(settings.groq_api_key, settings.model_id))

    if not chain:
        return UnavailableProvider(
            "neither WATSONX_API_KEY nor GROQ_API_KEY is set"
        )
    return FallbackProvider(chain)
