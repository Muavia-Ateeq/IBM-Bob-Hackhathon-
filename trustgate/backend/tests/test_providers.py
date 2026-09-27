"""The provider chain: IBM watsonx.ai primary, Groq fallback, both-fail closed.

The order is the product decision the hackathon is scored on, and it used to not exist —
`build_provider` was a single `if` on the Groq key, so an IBM key configured alone silently
degraded to no provider at all. These tests pin the three real cases: IBM serves, Groq
covers for IBM, and neither serving is a visible `ProviderUnavailable` rather than a
fabricated empty response.
"""

from __future__ import annotations

import asyncio
import sys
from dataclasses import replace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import Settings, load_settings
from app.llm.client import (
    Completion,
    FallbackProvider,
    ProviderUnavailable,
    StaticProvider,
    UnavailableProvider,
    build_provider,
)

SCHEMA = {"type": "object", "properties": {"findings": {"type": "array"}}, "required": ["findings"]}


class _Boom:
    """A provider that always fails, standing in for a real SDK or network error."""

    def __init__(self, model_id: str) -> None:
        self.model_id = model_id

    async def complete_json(self, system: str, user: str, schema: dict) -> Completion:
        raise ConnectionError(f"{self.model_id} is unreachable")


def _call(provider) -> Completion:
    return asyncio.run(provider.complete_json("system", "user", SCHEMA))


def test_ibm_serves_when_it_works_and_groq_is_never_called() -> None:
    ibm, groq = StaticProvider({"findings": []}, "ibm-primary"), StaticProvider({}, "groq-fallback")
    chain = FallbackProvider([ibm, groq])

    assert _call(chain).payload == {"findings": []}
    assert chain.model_id == "ibm-primary"
    assert groq.calls == 0, "Groq was consulted even though watsonx answered"


def test_groq_serves_when_ibm_fails() -> None:
    groq = StaticProvider({"findings": []}, "groq-fallback")
    chain = FallbackProvider([_Boom("ibm-primary"), groq])

    assert _call(chain).payload == {"findings": []}
    assert chain.model_id == "groq-fallback"
    assert groq.calls == 1


def test_both_failing_raises_with_both_reasons_and_never_a_fake_success() -> None:
    chain = FallbackProvider([_Boom("ibm-primary"), _Boom("groq-fallback")])

    with pytest.raises(ProviderUnavailable) as excinfo:
        _call(chain)

    message = str(excinfo.value)
    assert "ibm-primary" in message
    assert "groq-fallback" in message


def test_model_id_names_the_provider_that_actually_served() -> None:
    """Not the first one tried — the one that answered."""
    chain = FallbackProvider([_Boom("ibm-primary"), StaticProvider({}, "groq-fallback")])
    _call(chain)
    assert chain.model_id == "groq-fallback"

    unused = FallbackProvider([StaticProvider({}, "ibm-primary")])
    assert unused.model_id == "unresolved", "a chain that has served nothing must not claim a model"


def _settings(**overrides) -> Settings:
    """`load_settings` reads the ambient environment, which a test must not depend on."""
    return replace(load_settings(), **overrides)


def test_build_provider_orders_ibm_before_groq() -> None:
    settings = _settings(
        groq_api_key="g", watsonx_api_key="w", watsonx_model_id="ibm-model", model_id="groq-model"
    )
    chain = build_provider(settings)
    assert isinstance(chain, FallbackProvider)
    ids = [provider.model_id for provider in chain.providers]
    assert ids == sorted(ids, key=lambda m: 0 if m == settings.watsonx_model_id else 1)


def test_build_provider_with_no_keys_is_unavailable_not_a_fake_provider() -> None:
    provider = build_provider(_settings(groq_api_key=None, watsonx_api_key=None))
    assert isinstance(provider, UnavailableProvider)
    assert "WATSONX_API_KEY" in provider.reason
    assert "GROQ_API_KEY" in provider.reason


def test_ibm_without_project_or_space_is_reported_not_silently_half_configured() -> None:
    """watsonx.ai scopes a request to a project or a space; with neither, the SDK call is
    meaningless, so the chain drops IBM and says why rather than failing on the first request."""
    chain = build_provider(
        _settings(
            groq_api_key="g",
            watsonx_api_key="w",
            watsonx_project_id=None,
            watsonx_space_id=None,
        )
    )
    assert [p.model_id for p in chain.providers] == ["openai/gpt-oss-120b"]


def test_unavailable_provider_raises_rather_than_returning_empty() -> None:
    with pytest.raises(ProviderUnavailable):
        _call(UnavailableProvider("no key"))
