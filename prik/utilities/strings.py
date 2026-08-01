"""Small, self-contained helpers for generated identifiers."""

from __future__ import annotations

from itertools import count
from secrets import choice
from string import ascii_lowercase, digits
from typing import Protocol

__all__ = ("create_incremented_string", "random_string")

_RANDOM_ALPHABET = ascii_lowercase + digits


class _NameClashRules(Protocol):
    """Protocol for target-language-aware identifier collision checks."""

    def has_clash(self, name: object, symbols: set[object]) -> bool:
        """Return whether ``name`` cannot be used with ``symbols``."""


def random_string(length: int) -> str:
    """Return ``length`` random lower-case letters and decimal digits."""
    return "".join(choice(_RANDOM_ALPHABET) for _ in range(length))


def create_incremented_string(
    forbidden_exprs: set[object],
    prefix: str | None = "Dummy",
    counter: int = 2,
    naming_rules: _NameClashRules | None = None,
) -> tuple[str, int]:
    """Return the first available ``prefix_N`` name and next counter.

    ``naming_rules`` may implement case-insensitive or language-specific
    collision checks. Without it, membership in ``forbidden_exprs`` decides
    availability.
    """
    stem = "Dummy" if prefix is None else str(prefix)
    for number in count(counter):
        candidate = f"{stem}_{number}"
        clashes = naming_rules.has_clash(candidate, forbidden_exprs) if naming_rules else candidate in forbidden_exprs
        if not clashes:
            return candidate, number + 1
    raise RuntimeError("unreachable: an unbounded counter always yields a candidate")
