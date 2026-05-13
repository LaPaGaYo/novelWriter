"""
plotwright fork — Ollama provider
=================================

Local Ollama daemon. No SDK dependency; we hit the daemon's HTTP API
directly through `transport.make_client`. Uses `NoAuth` because the local
daemon is unauthenticated (it relies on localhost-only binding for security).

The default base URL `http://127.0.0.1:11434` matches Ollama's default
listener. The user can override per-instance via `provider_configs["ollama"]
["base_url"]` in `AIConfig`.

`is_local = True` so the privacy gate treats Ollama like MockProvider for
master-switch purposes (no network egress observable from outside the
machine).
"""
from __future__ import annotations

from typing import Any

from novelwriter.ai.auth import NoAuth
from novelwriter.ai.provider.base import Provider, ProviderError, ProviderResponse
from novelwriter.ai.tokens import estimate_tokens


_DEFAULT_BASE_URL = "http://127.0.0.1:11434"
_DEFAULT_MODEL = "llama3.1"


class OllamaProvider(Provider):
    """Local Ollama provider.

    Instantiation never opens a socket. The first network event is the user's
    first `generate()` or `health_check()` call.
    """

    def __init__(
        self,
        *,
        base_url: str = _DEFAULT_BASE_URL,
        model: str = _DEFAULT_MODEL,
        transport: Any = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._transport = transport
        self.auth = NoAuth()
        self._client: Any = None  # lazily built

    @property
    def name(self) -> str:
        return f"ollama:{self._model}"

    @property
    def is_local(self) -> bool:
        return True

    def _make_client(self):
        if self._client is None:
            # Import lazily so transport.py (and httpx) only lands when this
            # provider is actually used.
            from novelwriter.ai.transport import make_client
            self._client = make_client(
                base_url=self._base_url,
                transport=self._transport,
                headers=self.auth.headers(),
            )
        return self._client

    def generate(self, prompt: str, **opts: object) -> ProviderResponse:
        client = self._make_client()
        try:
            resp = client.post(
                "/api/generate",
                json={"model": self._model, "prompt": prompt, "stream": False},
            )
            resp.raise_for_status()
            payload = resp.json()
        except Exception as exc:  # noqa: BLE001 - wrap once for the boundary
            raise ProviderError(f"Ollama generate failed: {exc}") from exc
        text = payload.get("response", "") if isinstance(payload, dict) else ""
        return ProviderResponse(
            text=text,
            provider_name=self.name,
            is_local=self.is_local,
            estimated_tokens_in=estimate_tokens(prompt),
            estimated_tokens_out=estimate_tokens(text),
        )

    def estimate_tokens(self, text: str) -> int:
        # Local model; user is not metered. Heuristic is sufficient and
        # avoids pulling a tokenizer SDK for privacy reasons.
        return estimate_tokens(text)

    def health_check(self) -> bool:
        """Probe the daemon's `/api/tags` endpoint."""
        client = self._make_client()
        try:
            resp = client.get("/api/tags")
            return resp.status_code == 200
        except Exception:
            return False


__all__ = ["OllamaProvider"]
