"""
Plotwright – Single-Egress Static Check (Sprint 1, gate item 11)
=================================================================

Hard gate: ``httpx`` and ``requests`` may only be imported from
``novelwriter/ai/network.py``. Any other import is a privacy regression
because it bypasses the gate that proves the network-zero contract.

This test parses every ``.py`` file under ``novelwriter/`` with
:mod:`ast` and checks every ``import`` / ``from ... import`` statement.
``ast`` is used (not regex) so we do not flag mentions in string literals
or comments.

File History:
Created: 2026-04-26 [Sprint 1]
"""
from __future__ import annotations

import ast

from pathlib import Path

import pytest

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent / "novelwriter"
_ALLOWED_FILE = (_PACKAGE_ROOT / "ai" / "network.py").resolve()
_FORBIDDEN_TOP_LEVEL_PACKAGES = frozenset({"httpx", "requests"})


def _collect_imports(tree: ast.AST) -> set[str]:
    """Return the top-level package names imported anywhere in the tree."""
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                continue  # relative import: not an external package
            if node.module:
                found.add(node.module.split(".", 1)[0])
    return found


def test_no_httpx_or_requests_outside_network_gate() -> None:
    offenders: list[tuple[Path, set[str]]] = []
    for path in _PACKAGE_ROOT.rglob("*.py"):
        if path.resolve() == _ALLOWED_FILE:
            continue  # the single legitimate egress point
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:  # pragma: no cover — defensive
            pytest.fail(f"Could not parse {path}: {exc}")

        forbidden = _collect_imports(tree) & _FORBIDDEN_TOP_LEVEL_PACKAGES
        if forbidden:
            offenders.append((path, forbidden))

    assert offenders == [], (
        "Single-egress contract violated. "
        "httpx/requests may only be imported from novelwriter/ai/network.py.\n"
        + "\n".join(f"  {p}: {sorted(packages)}" for p, packages in offenders)
    )
