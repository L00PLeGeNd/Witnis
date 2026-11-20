"""Seam: auto GT filters reject keyword/noise implements (FAILURE_CASES F2)."""

from __future__ import annotations

from witnis.core.gt_filters import is_noise_edge


def test_rejects_for_implements_serializable() -> None:
    assert is_noise_edge(
        "implements",
        "src/Foo.java:for",
        "Serializable",
    )


def test_keeps_real_implements() -> None:
    assert not is_noise_edge(
        "implements",
        "src/JdbcUserRepository.java:JdbcUserRepository",
        "UserRepository",
    )
