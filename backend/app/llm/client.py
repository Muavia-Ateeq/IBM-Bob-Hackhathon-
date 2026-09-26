from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol

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


def build_provider(settings: Settings) -> Provider:
    if not settings.groq_api_key:
        return UnavailableProvider("GROQ_API_KEY is not set")
    return GroqProvider(settings.groq_api_key, settings.model_id)
