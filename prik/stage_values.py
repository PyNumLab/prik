"""Editable stage outputs with consumer-owned recursive freezing."""

from __future__ import annotations

from dataclasses import fields
from types import MappingProxyType
from typing import TypeVar


_StageRecordT = TypeVar("_StageRecordT", bound="StageRecord")


class FrozenStageRecordError(TypeError):
    """Raised when code changes a record after its consumer freezes it."""


class StageRecord:
    """Mutable stage output that its next consumer can recursively freeze."""

    _stage_frozen = False

    def __setattr__(self, name: str, value: object) -> None:
        """Reject changes once the receiving stage owns this record."""
        if name != "_stage_frozen" and self._stage_frozen:
            raise FrozenStageRecordError(f"{type(self).__name__} is frozen by its consuming stage")
        object.__setattr__(self, name, value)

    def freeze(self: _StageRecordT) -> _StageRecordT:
        """Recursively freeze this record and return the consumed input."""
        if self._stage_frozen:
            return self
        for descriptor in fields(self):
            object.__setattr__(self, descriptor.name, self._freeze_value(getattr(self, descriptor.name)))
        object.__setattr__(self, "_stage_frozen", True)
        return self

    @staticmethod
    def _freeze_value(value: object) -> object:
        """Recursively make one nested stage value immutable."""
        if isinstance(value, StageRecord):
            return value.freeze()
        if isinstance(value, tuple):
            return tuple(StageRecord._freeze_value(item) for item in value)
        if isinstance(value, list):
            return tuple(StageRecord._freeze_value(item) for item in value)
        if isinstance(value, dict):
            return MappingProxyType({key: StageRecord._freeze_value(item) for key, item in value.items()})
        if isinstance(value, set):
            return frozenset(StageRecord._freeze_value(item) for item in value)
        return value
