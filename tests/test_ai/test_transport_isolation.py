"""
plotwright fork — Transport isolation test (Sprint 2, SC-8)
============================================================

Source-level enforcement of the contract:

    "no `import httpx` or `import requests` outside `novelwriter/ai/transport.py`"

This is the static counterpart to `test_privacy.py`'s runtime checks. Even
though `test_provider_construction_offline.py` catches the runtime symptom
(socket activity) and `test_privacy.py` catches the SDK-leak symptom
(`sys.modules`), neither of them fires when a contributor *writes* a
forbidden import. AST scanning fails loud at the source level, before the
runtime test has a chance to.

Why AST and not regex: a docstring or comment that mentions ``import httpx``
must not false-positive. We parse the module and inspect ``ast.Import`` /
``ast.ImportFrom`` nodes only.

Scope: every ``.py`` file directly under

    novelwriter/ai/provider/
    novelwriter/ai/__init__.py

is scanned. ``novelwriter/ai/transport.py`` is explicitly the only file
allowed to import ``httpx``; that file is excluded from the scan.

Failure mode: the assertion lists the offending file:line for each
violation. Recovery is always the same — route the HTTP call through
``transport.build_cloud_client()`` and let ``transport.py`` own the
``httpx`` import.
"""
from __future__ import annotations

import ast

from pathlib import Path


# Modules whose top-level (or any-level) import is forbidden.
_FORBIDDEN_TOP_LEVEL = frozenset({"httpx", "requests"})

# The only file in the AI substrate allowed to import httpx.
_ALLOWED_OWNERS = frozenset({"transport.py"})


def _root() -> Path:
    """Return the novelwriter/ai/ source root, independent of cwd."""
    here = Path(__file__).resolve()
    # tests/test_ai/test_transport_isolation.py  -> repo_root/novelwriter/ai/
    return here.parents[2] / "novelwriter" / "ai"


def _scan_targets() -> list[Path]:
    """Files in scope of the SC-8 lint rule.

    The contract names ``novelwriter/ai/provider/`` explicitly; we also
    include ``novelwriter/ai/__init__.py`` because that is the substrate's
    public import surface and a top-level ``import httpx`` there would
    re-introduce eager-network risk.
    """
    ai_root = _root()
    targets: list[Path] = []
    provider_dir = ai_root / "provider"
    if provider_dir.is_dir():
        targets.extend(sorted(provider_dir.glob("*.py")))
    init_py = ai_root / "__init__.py"
    if init_py.exists():
        targets.append(init_py)
    return targets


def _collect_forbidden_imports(path: Path) -> list[tuple[int, str]]:
    """Return ``(lineno, module_name)`` pairs for forbidden imports in ``path``.

    Walks the AST and inspects ``import X`` / ``from X import ...`` only.
    Comments, docstrings, and string literals that mention ``httpx`` do
    not trigger a violation.
    """
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    violations: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".", 1)[0]
                if top in _FORBIDDEN_TOP_LEVEL:
                    violations.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                # Relative imports like `from . import foo` — out of scope.
                continue
            top = node.module.split(".", 1)[0]
            if top in _FORBIDDEN_TOP_LEVEL:
                violations.append((node.lineno, node.module))
    return violations


def test_no_httpx_or_requests_outside_transport():
    """SC-8: only ``transport.py`` may import ``httpx`` or ``requests``."""
    targets = _scan_targets()
    assert targets, "transport-isolation scan found no target files (path bug?)"

    failures: list[str] = []
    for path in targets:
        if path.name in _ALLOWED_OWNERS:
            # Defensive: __init__.py and provider/*.py never overlap with
            # transport.py, but this keeps the rule legible.
            continue
        for lineno, module in _collect_forbidden_imports(path):
            failures.append(f"{path}:{lineno}: forbidden import of `{module}`")

    if failures:
        joined = "\n  ".join(failures)
        raise AssertionError(
            "SC-8 transport-isolation violation. The AI substrate must "
            "route every HTTP call through novelwriter/ai/transport.py. "
            "Offending imports:\n  "
            + joined
            + "\n\nFix: replace the direct import with "
            "`from novelwriter.ai.transport import build_cloud_client`."
        )


def test_transport_py_is_the_sole_owner():
    """Companion assertion: ``transport.py`` actually imports ``httpx``.

    Guards against the inverse regression — the lint rule passing
    vacuously because someone removed ``transport.py`` or stopped using
    ``httpx`` there. If this fails, the substrate is using some other
    HTTP client, which is a separate (also bad) outcome that should be
    caught at the same gate.
    """
    transport = _root() / "transport.py"
    assert transport.exists(), "novelwriter/ai/transport.py is missing"
    imports = _collect_forbidden_imports(transport)
    httpx_imports = [m for _, m in imports if m.split(".", 1)[0] == "httpx"]
    assert httpx_imports, (
        "transport.py does not import httpx. Either the substrate switched "
        "HTTP clients (update this assertion) or the import was deleted by "
        "mistake."
    )
