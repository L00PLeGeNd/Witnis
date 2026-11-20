"""Filters for auto ground-truth / noisy Java relation endpoints (F2/F3)."""

from __future__ import annotations

_JAVA_NOISE_NAMES = {
    "for",
    "if",
    "while",
    "switch",
    "catch",
    "try",
    "new",
    "return",
    "class",
    "this",
    "super",
    "var",
    "record",
}


def relation_endpoint_leaf(symbol: str) -> str:
    part = symbol.split(":")[-1] if ":" in symbol else symbol
    return part.split(".")[-1]


def is_noise_edge(relation_type: str, source: str, target: str) -> bool:
    """True when an auto label should not promote this edge."""
    src = relation_endpoint_leaf(source)
    tgt = relation_endpoint_leaf(target)
    if not src or not tgt:
        return True
    if src.lower() in _JAVA_NOISE_NAMES or tgt.lower() in _JAVA_NOISE_NAMES:
        return True
    if len(src) <= 2 and relation_type in {"implements", "inherits", "calls"}:
        return True
    # Tautological self edge
    if src == tgt and relation_type == "calls":
        return True
    return False
