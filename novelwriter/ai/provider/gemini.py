"""
plotwright fork — Gemini provider
=================================

Gemini supports two auth modes: API key (`ApiKeyAuth` with the
`x-goog-api-key` header) and OAuth ("Sign in with Google", via `OAuthCreds`
with a `Authorization: Bearer …` header). The provider does not need to
care which one is active — it just merges `auth.headers()` into the
outgoing request.

Like the other cloud providers, we hit the HTTP API directly through
`transport.make_client` rather than via the `google-generativeai` SDK,
because the SDK eagerly probes the network at import time. Going REST-only
keeps `import novelwriter.ai` free of any network discovery.

Sprint 2 ships only a non-streaming `generateContent` call.
"""
from __future__ import annotations

from typing import Any

from novelwriter.ai.auth import ApiKeyAuth, Auth, OAuthCreds
from novelwriter.ai.provider.base import (
    Provider,
    ProviderError,
    ProviderResponse,
)
from novelwriter.ai.tokenizers import for_provider


_DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com"
_DEFAULT_MODEL = "gemini-2.5-flash"


# Gemini OAuth scope — pinned per the Sprint 2 design contract.
GEMINI_SCOPE = "https://www.googleapis.com/auth/generative-language"


class GeminiProvider(Provider):
    """Google Gemini cloud provider.

    Construction never opens a socket. The `google-generativeai` SDK is not
    imported anywhere in this module — the privacy test asserts that
    `import novelwriter.ai` leaves `google` and `google.generativeai` out of
    `sys.modules`.
    """

    def __init__(
        self,
        *,
        auth: Auth,
        model: str = _DEFAULT_MODEL,
        base_url: str = _DEFAULT_BASE_URL,
        transport: Any = None,
    ) -> None:
        if not isinstance(auth, (ApiKeyAuth, OAuthCreds)):
            raise ProviderError(
                "Gemini provider requires ApiKeyAuth or OAuthCreds; "
                f"got {type(auth).__name__}",
            )
        self.auth = auth
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._transport = transport
        self._tokenize = for_provider("gemini")
        self._client: Any = None

    @property
    def name(self) -> str:
        return f"gemini:{self._model}"

    @property
    def is_local(self) -> bool:
        return False

    def _make_client(self):
        if self._client is None:
            from novelwriter.ai.transport import make_client
            headers = dict(self.auth.headers())
            headers["content-type"] = "application/json"
            self._client = make_client(
                base_url=self._base_url,
                transport=self._transport,
                headers=headers,
            )
        return self._client

    def generate(self, prompt: str, **opts: object) -> ProviderResponse:
        # Refresh OAuth tokens defensively at call-start. ApiKeyAuth is a
        # no-op; OAuthCreds checks expiry and refreshes if within
        # `REFRESH_WINDOW`. Refresh failures propagate as ProviderError so
        # the status bar can surface an error state.
        try:
            self.auth.refresh_if_needed()
        except Exception as exc:
            raise ProviderError(f"Gemini auth refresh failed: {exc}") from exc

        # If OAuth refreshed the bearer token, rebuild the client headers so
        # the new token rides the next request. Cheaper than introspecting
        # the existing client's header state.
        self._client = None
        client = self._make_client()

        try:
            resp = client.post(
                f"/v1beta/models/{self._model}:generateContent",
                json={"contents": [{"parts": [{"text": prompt}]}]},
            )
            resp.raise_for_status()
            payload = resp.json()
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(f"Gemini generate failed: {exc}") from exc

        text = _extract_gemini_text(payload)
        return ProviderResponse(
            text=text,
            provider_name=self.name,
            is_local=self.is_local,
            estimated_tokens_in=self.estimate_tokens(prompt),
            estimated_tokens_out=self.estimate_tokens(text),
        )

    def estimate_tokens(self, text: str) -> int:
        return self._tokenize(text)

    def health_check(self) -> bool:
        # Lightweight check: we have credentials of some kind and they're
        # not visibly stale. A future iteration may issue a no-cost
        # `models.list` call once we measure latency impact.
        return bool(self.auth.headers())


def _extract_gemini_text(payload: Any) -> str:
    """Pull the first text part out of a Gemini generateContent response.

    Response shape is
    `{"candidates": [{"content": {"parts": [{"text": "..."}]}}, ...]}`.
    """
    if not isinstance(payload, dict):
        return ""
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        return ""
    content = candidates[0].get("content") if isinstance(candidates[0], dict) else None
    parts = content.get("parts") if isinstance(content, dict) else None
    if not isinstance(parts, list):
        return ""
    for part in parts:
        if isinstance(part, dict):
            text = part.get("text", "")
            if isinstance(text, str) and text:
                return text
    return ""


__all__ = ["GEMINI_SCOPE", "GeminiProvider"]
