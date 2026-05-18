"""
plotwright fork — Provider Registry
===================================

Maps provider-name strings to factory callables. `AIConfig.providers` stores
just the string id (`"mock"`, `"ollama"`, `"anthropic"`, `"gemini"`); the
registry resolves that string to a concrete `Provider` instance using the
per-provider settings slice from `AIConfig.provider_configs` plus any
secrets resolved through the keychain.

The registry is the only place where the AI substrate decides which provider
to instantiate. Adding a provider in S6 (OpenAI) means: write `openai.py`
and append one entry to `_FACTORIES`. No other call site changes.

Imports of the concrete provider modules are deferred to factory call time
so a fork that never wires Anthropic/Gemini at runtime keeps those modules
out of `sys.modules` even though the registry itself is imported.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from novelwriter.ai.provider.base import Provider, ProviderError

if TYPE_CHECKING:
    from novelwriter.ai.config import AIFeature
    from novelwriter.ai.network import NetworkGate


# Factory: takes the per-provider settings dict, a KeyStore-or-None, and
# optional gate + feature kwargs, returning an instantiated `Provider`. The
# gate is threaded through to cloud providers so generate() can call
# `gate.guard(feature)` before any client work (S-1 privacy contract).
ProviderFactory = Callable[..., Provider]


def _make_mock(
    settings: dict[str, Any],
    keystore: Any,
    *,
    gate: "NetworkGate | None" = None,
    feature: "AIFeature | None" = None,
) -> Provider:
    # MockProvider takes no config and no gate; settings + gate are ignored.
    # Mock is test-only and never makes a real network call.
    from novelwriter.ai.provider.mock import MockProvider
    return MockProvider()


def _make_ollama(
    settings: dict[str, Any],
    keystore: Any,
    *,
    gate: "NetworkGate | None" = None,
    feature: "AIFeature | None" = None,
) -> Provider:
    from novelwriter.ai.provider.ollama import OllamaProvider
    return OllamaProvider(
        base_url=settings.get("base_url", "http://127.0.0.1:11434"),
        model=settings.get("model", "llama3.1"),
        gate=gate,
        feature=feature,
    )


def _make_anthropic(
    settings: dict[str, Any],
    keystore: Any,
    *,
    gate: "NetworkGate | None" = None,
    feature: "AIFeature | None" = None,
) -> Provider:
    from novelwriter.ai.provider.anthropic import AnthropicProvider
    api_key = _read_api_key(keystore, "anthropic", settings)
    if not api_key:
        raise ProviderError("Anthropic API key not configured")
    return AnthropicProvider(
        api_key=api_key,
        model=settings.get("model", "claude-sonnet-4-5"),
        gate=gate,
        feature=feature,
    )


def _make_gemini(
    settings: dict[str, Any],
    keystore: Any,
    *,
    gate: "NetworkGate | None" = None,
    feature: "AIFeature | None" = None,
) -> Provider:
    from novelwriter.ai.provider.gemini import GeminiProvider
    auth_mode = settings.get("auth_mode", "api_key")
    if auth_mode == "oauth":
        # OAuth path: rehydrate `OAuthCreds` from the keychain blob.
        # The OAuth module owns the refresher closure that knows how to call
        # Google's token endpoint, so the registry delegates rehydration to
        # `oauth.creds_from_blob`.
        from novelwriter.ai.oauth import creds_from_blob
        blob = keystore.get_oauth("gemini") if keystore else None
        if not blob:
            raise ProviderError("Gemini OAuth not configured; sign in first")
        auth = creds_from_blob(blob, transport=settings.get("_oauth_transport"))
    else:
        from novelwriter.ai.auth import ApiKeyAuth
        api_key = _read_api_key(keystore, "gemini", settings)
        if not api_key:
            raise ProviderError("Gemini API key not configured")
        auth = ApiKeyAuth(api_key=api_key, header_name="x-goog-api-key")
    return GeminiProvider(
        auth=auth,
        model=settings.get("model", "gemini-2.5-flash"),
        gate=gate,
        feature=feature,
    )


def _read_api_key(keystore: Any, provider_id: str, settings: dict[str, Any]) -> str | None:
    """Resolve an API key for `provider_id`.

    Preference order:
    1. Keychain entry (production path).
    2. `settings["api_key"]` (test override; never written by the real UI).
    """
    if keystore is not None:
        try:
            key = keystore.get(provider_id)
            if key:
                return key
        except Exception:
            # Keychain failures fall through to the settings override; the
            # caller decides whether to surface a re-prompt.
            pass
    return settings.get("api_key")


_FACTORIES: dict[str, ProviderFactory] = {
    "mock": _make_mock,
    "ollama": _make_ollama,
    "anthropic": _make_anthropic,
    "gemini": _make_gemini,
}


def available_providers() -> tuple[str, ...]:
    """Return the tuple of registered provider ids."""
    return tuple(_FACTORIES.keys())


def make_provider(
    provider_id: str,
    *,
    settings: dict[str, Any] | None = None,
    keystore: Any = None,
    gate: "NetworkGate | None" = None,
    feature: "AIFeature | None" = None,
) -> Provider:
    """Instantiate a provider by id.

    `settings` is the per-provider slice of `AIConfig.provider_configs`.
    `keystore` is the keychain reader; pass `FakeKeyStore()` in tests.

    `gate` + `feature` thread through to the provider so `generate()` calls
    `gate.guard(feature)` before any client work. Production sites (the AI
    Preferences "Dry-run" handler, future feature handlers) MUST pass both
    so the privacy contract is enforced. Tests may omit them; constructed
    providers without a gate behave as before for test-only paths.

    Raises `ProviderError` if the id is unknown, required secrets are
    missing, or gate+feature are partially configured (one without the
    other is misconfiguration). The caller surfaces the error to the user.
    """
    settings = dict(settings or {})
    base = provider_id.split(":", 1)[0].lower()
    factory = _FACTORIES.get(base)
    if factory is None:
        raise ProviderError(
            f"Unknown provider {provider_id!r}; registered providers: "
            f"{sorted(_FACTORIES)}",
        )
    return factory(settings, keystore, gate=gate, feature=feature)


__all__ = [
    "ProviderFactory",
    "available_providers",
    "make_provider",
]
