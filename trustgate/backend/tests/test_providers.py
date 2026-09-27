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


def test_build_provider_orders_ibm_before_groq(monkeypatch: pytest.MonkeyPatch) -> None:
    """The order is the product decision, so it is asserted on a chain that really has two.

    Without stubbing, a project-less configuration drops IBM and the assertion would hold on a
    one-element list — a test that passes while proving nothing. `build_provider` imports
    WatsonxProvider inside the function, so patching the module attribute is what it reads.
    """
    import app.llm.watsonx_client as watsonx

    class _StubWatsonx:
        def __init__(self, api_key: str, model_id: str, url: str, project_id=None, space_id=None) -> None:
            self.model_id = model_id

    monkeypatch.setattr(watsonx, "WatsonxProvider", _StubWatsonx)

    chain = build_provider(
        _settings(
            groq_api_key="g",
            watsonx_api_key="w",
            watsonx_model_id="ibm-model",
            model_id="groq-model",
            watsonx_project_id="proj",
        )
    )
    assert isinstance(chain, FallbackProvider)
    assert [p.model_id for p in chain.providers] == ["ibm-model", "groq-model"]


def test_a_rejected_ibm_key_falls_through_to_groq_instead_of_crashing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression: `ModelInference(...)` authenticates against IAM in its constructor.

    An invalid key raises `InvalidCredentialsError`, which is NOT a ProviderUnavailable, so
    before the translation in `WatsonxProvider.__init__` it escaped `build_provider` entirely
    and killed the whole run — a bad IBM key took down the gate instead of falling back to the
    provider that exists to cover for exactly that. Observed live: the SDK's real error is
    `BXNIM0415E Provided API key could not be found.`
    """
    import ibm_watsonx_ai.foundation_models as foundation_models

    class _InvalidCredentialsError(Exception):
        pass

    def _reject(*args, **kwargs):
        raise _InvalidCredentialsError("BXNIM0415E Provided API key could not be found.")

    monkeypatch.setattr(foundation_models, "ModelInference", _reject)

    chain = build_provider(
        _settings(
            groq_api_key="g",
            watsonx_api_key="bad",
            watsonx_project_id="proj",
            watsonx_model_id="ibm-model",
            model_id="groq-model",
        )
    )
    assert isinstance(chain, FallbackProvider)
    assert [p.model_id for p in chain.providers] == ["groq-model"], (
        "a rejected IBM credential must leave Groq serving, not abort the run"
    )


def test_build_provider_with_no_keys_is_unavailable_not_a_fake_provider() -> None:
    provider = build_provider(_settings(groq_api_key=None, watsonx_api_key=None))
    assert isinstance(provider, UnavailableProvider)
    assert "WATSONX_API_KEY" in provider.reason
    assert "GROQ_API_KEY" in provider.reason


def test_ibm_without_project_or_space_is_reported_not_silently_half_configured() -> None:
    """watsonx.ai scopes a request to a project or a space; with neither, the SDK call is
    meaningless, so the chain drops IBM and says why rather than failing on the first request."""
    settings = _settings(
        groq_api_key="g",
        watsonx_api_key="w",
        watsonx_project_id=None,
        watsonx_space_id=None,
        model_id="groq-model",
    )
    chain = build_provider(settings)
    assert [p.model_id for p in chain.providers] == ["groq-model"]


def test_unavailable_provider_raises_rather_than_returning_empty() -> None:
    with pytest.raises(ProviderUnavailable):
        _call(UnavailableProvider("no key"))
