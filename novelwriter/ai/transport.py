"""
plotwright fork — HTTP Transport Factory
========================================

The single place inside `novelwriter/ai/` that imports `httpx`. Every cloud
provider must obtain its HTTP client from `make_client()` rather than
constructing `httpx.Client` directly. A CI lint rule asserts that no file
under `novelwriter/ai/provider/` imports `httpx` or `requests`.

The privacy benefit: one chokepoint owns timeouts, redirect policy, default
headers, and (in tests) injection of `httpx.MockTransport`. The contract
suite parametrizes over cloud providers by supplying a `MockTransport` so no
network is ever required for `test_provider_contract.py` or
`test_provider_construction_offline.py`.
"""
from __future__ import annotations

import httpx

# Default per-request timeout. Generous so a slow first-token from a remote
# model does not kill a legitimate call, but bounded so a stuck connection
# does not lock the UI thread forever. Override per-call by passing
# `timeout=httpx.Timeout(...)` to the request methods.
_DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0)


def make_client(
    *,
    base_url: str | None = None,
    transport: httpx.BaseTransport | None = None,
    headers: dict[str, str] | None = None,
    timeout: httpx.Timeout | None = None,
) -> httpx.Client:
    """Build a `httpx.Client` for a cloud provider.

    The `transport` parameter exists so tests can inject `httpx.MockTransport`
    without monkey-patching. Production callers leave it as None and httpx
    picks its default `HTTPTransport`.

    `headers` are merged into every request; provider modules pass their
    `auth.headers()` here so the authentication header rides every outbound
    call without per-call boilerplate.

    `redirects` are NOT followed by default. Providers do not redirect under
    normal API operation; an unexpected redirect is a signal to investigate,
    not silently follow.
    """
    return httpx.Client(
        base_url=base_url or "",
        transport=transport,
        headers=headers or {},
        timeout=timeout or _DEFAULT_TIMEOUT,
        follow_redirects=False,
        trust_env=False,  # ignore HTTP(S)_PROXY env; the user opts in explicitly
    )


__all__ = ["make_client"]
