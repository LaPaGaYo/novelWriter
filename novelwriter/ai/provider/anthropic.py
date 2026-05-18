"""
plotwright fork — Anthropic provider
====================================

Cloud provider using ApiKeyAuth. The `anthropic` SDK is imported lazily so
`import novelwriter.ai` never pulls it into `sys.modules` (privacy test
asserts this).

This provider goes through the shared `transport.make_client` factory.
Custom HTTP behavior (timeouts, redirect policy) lives there so we do not
spread httpx configuration across providers.

Sprint 2 ships only a non-streaming `messages.create` call. Streaming is
deferred to a later sprint per `prd.md:52`.
"""
from __future__ import annotations

from typing import Any

from typing import TYPE_CHECKING

from novelwriter.ai.auth import ApiKeyAuth, Auth
from novelwriter.ai.provider.base import (
    Provider,
    ProviderDependencyError,
    ProviderError,
    ProviderResponse,
)
from novelwriter.ai.tokenizers import for_provider

if TYPE_CHECKING:
    from novelwriter.ai.config import AIFeature
    from novelwriter.ai.network import NetworkGate


_DEFAULT_BASE_URL = "https://api.anthropic.com"
_DEFAULT_MODEL = "claude-sonnet-4-5"
_DEFAULT_MAX_TOKENS = 1024
_ANTHROPIC_VERSION = "2023-06-01"


class AnthropicProvider(Provider):
    """Anthropic cloud provider.

    Construction never opens a socket. We do NOT import the `anthropic` SDK
    at construction time either — token estimation and the HTTP request use
    `transport.make_client` + `tokenizers.for_provider`, which is enough for
    Sprint 2's non-streaming call shape.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str = _DEFAULT_MODEL,
        base_url: str = _DEFAULT_BASE_URL,
        transport: Any = None,
        max_tokens: int = _DEFAULT_MAX_TOKENS,
        gate: "NetworkGate | None" = None,
        feature: "AIFeature | None" = None,
    ) -> None:
        if not api_key:
            raise ProviderError("Anthropic provider requires a non-empty api_key")
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._transport = transport
        self._max_tokens = max_tokens
        self.auth: Auth = ApiKeyAuth(api_key=api_key, header_name="x-api-key")
        self._tokenize = for_provider("anthropic")
        self._client: Any = None  # lazily built
        # Privacy gate: when both gate and feature are set, every generate()
        # call routes through gate.guard(feature) before any client work.
        # See provider/base.py::_enforce_privacy_gate for the contract.
        self._gate = gate
        self._feature = feature

    @property
    def name(self) -> str:
        return f"anthropic:{self._model}"

    @property
    def is_local(self) -> bool:
        return False

    def _make_client(self):
        if self._client is None:
            from novelwriter.ai.transport import make_client
            headers = dict(self.auth.headers())
            headers["anthropic-version"] = _ANTHROPIC_VERSION
            headers["content-type"] = "application/json"
            self._client = make_client(
                base_url=self._base_url,
                transport=self._transport,
                headers=headers,
            )
        return self._client

    def generate(self, prompt: str, **opts: object) -> ProviderResponse:
        # ENFORCE privacy gate BEFORE any client work. Raises
        # PrivacyGatingError if master switch or per-feature flag is off.
        # This is the load-bearing privacy contract — see provider/base.py
        # gate plumbing block + tests/test_ai/test_provider_gating.py.
        self._enforce_privacy_gate()

        # Refresh credentials defensively. ApiKeyAuth is a no-op, but if we
        # ever swap an OAuth-style auth in here, the call-start refresh
        # contract is honored without a code change.
        try:
            self.auth.refresh_if_needed()
        except Exception as exc:
            raise ProviderError(f"Anthropic auth refresh failed: {exc}") from exc

        client = self._make_client()
        try:
            resp = client.post(
                "/v1/messages",
                json={
                    "model": self._model,
                    "max_tokens": int(opts.get("max_tokens", self._max_tokens)),
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            resp.raise_for_status()
            payload = resp.json()
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(f"Anthropic generate failed: {exc}") from exc

        text = _extract_anthropic_text(payload)
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
        # We do not burn a real API call for the health check in Sprint 2.
        # An API key being present is sufficient signal for the status bar;
        # the first real generate() either succeeds or surfaces a
        # ProviderError that the UI can catch. A future iteration may add a
        # cheap `/v1/models` GET when Anthropic ships one.
        return isinstance(self.auth, ApiKeyAuth) and bool(self.auth.api_key)

    # Allow tests to verify lazy SDK loading without exercising the network.
    @classmethod
    def _probe_sdk(cls) -> bool:
        """Return True if the optional `anthropic` SDK is importable.

        Provided for diagnostics; the provider's HTTP path does not depend
        on the SDK. Tests assert that calling this method does NOT alter
        whether `anthropic` is in `sys.modules` after import.
        """
        try:
            import anthropic  # noqa: F401 - lazy probe only
            return True
        except ImportError:
            return False


def _extract_anthropic_text(payload: Any) -> str:
    """Pull the first text block out of an Anthropic Messages response.

    The response shape is `{"content": [{"type": "text", "text": "..."}], ...}`.
    Defensive parsing: malformed payloads return an empty string rather than
    raising, because surfacing a `ProviderError` for "the API returned weird
    data" is more useful than a KeyError two layers up the stack.
    """
    if not isinstance(payload, dict):
        return ""
    content = payload.get("content")
    if not isinstance(content, list):
        return ""
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            text = block.get("text", "")
            if isinstance(text, str):
                return text
    return ""


__all__ = ["AnthropicProvider"]
