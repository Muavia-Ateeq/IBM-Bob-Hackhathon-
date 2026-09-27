from __future__ import annotations

import asyncio
import json
from typing import Any

from app.llm.client import Completion, ProviderUnavailable

MAX_RETRIES = 1


class WatsonxProvider:
    """IBM watsonx.ai inference. The primary provider; Groq is the fallback.

    The call shape was read from the installed SDK, not from a tutorial: introspecting
    `ibm_watsonx_ai` 1.7.2 gives
    `ModelInference(*, model_id, credentials, project_id, space_id, max_retries, ...)`
    and `.chat(messages: list[dict], params: dict | TextChatParameters | None) -> dict`,
    returning `{"choices": [{"message": {"content": ...}}]}`.

    `ModelInference` is NOT a top-level export of `ibm_watsonx_ai` in 1.7.2 — it lives in
    `ibm_watsonx_ai.foundation_models`. An earlier version of this file imported it from the
    top level and raised ImportError the first time it was ever constructed.

    `max_retries` is set to 1 deliberately. The SDK default is 10 with exponential backoff,
    which inside the checker's 30s `asyncio.wait_for` budget would surface as a TIMEOUT
    rather than an error — and a timeout never reaches the Groq fallback. One retry keeps a
    transient blip survivable while a real failure still arrives inside the budget.

    `chat()` returns no token usage, so `Completion` token counts stay 0. `checkers/semantic.py`
    already discards them, so nothing downstream is starved by that.

    UNVERIFIED — no watsonx credential has ever existed in this environment, so no call has
    been made. Whether `ibm/granite-4-h-small` honours `response_format` strict mode is
    therefore unknown; if it returns best-effort JSON instead, the Pydantic validation and the
    verbatim-evidence check in `semantic.py` still run, so a non-conforming response becomes a
    checker ERROR and the verdict degrades to REVIEW. It cannot reach PASS.
    """

    def __init__(
        self,
        api_key: str,
        model_id: str,
        url: str,
        project_id: str | None = None,
        space_id: str | None = None,
    ) -> None:
        try:
            from ibm_watsonx_ai import Credentials
            from ibm_watsonx_ai.foundation_models import ModelInference
        except ImportError as exc:
            raise ProviderUnavailable(f"ibm-watsonx-ai is not installed: {exc}") from exc

        if not project_id and not space_id:
            raise ProviderUnavailable(
                "WATSONX_PROJECT_ID or WATSONX_SPACE_ID is not set; "
                "watsonx.ai requires one to scope the request"
            )

        self._model = ModelInference(
            model_id=model_id,
            credentials=Credentials(url=url, api_key=api_key),
            project_id=project_id,
            space_id=space_id,
            max_retries=MAX_RETRIES,
        )
        self.model_id = model_id

    async def complete_json(self, system: str, user: str, schema: dict[str, Any]) -> Completion:
        response = await asyncio.to_thread(
            self._model.chat,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            params={
                "temperature": 0,
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "trustgate_findings",
                        "strict": True,
                        "schema": schema,
                    },
                },
            },
        )
        content = response["choices"][0]["message"]["content"] or "{}"
        return Completion(payload=json.loads(content))
