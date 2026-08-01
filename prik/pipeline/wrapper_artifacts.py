"""Generated-wrapper artifact handoff shared by wrapper build routes."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from prik.stage_values import StageRecord

__all__ = (
    "GeneratedSourceFile",
    "GeneratedWrapperArtifacts",
    "RenderedGeneratedWrapperArtifacts",
)


@dataclass
class GeneratedSourceFile(StageRecord):
    """One rendered generated source payload before it is written to disk."""

    path: Path
    text: str


@dataclass
class GeneratedWrapperArtifacts(StageRecord):
    """Generated wrapper files produced before compile/link orchestration."""

    module_name: str
    bridge_sources: tuple[Path, ...] = ()
    binding_sources: tuple[Path, ...] = ()
    header_files: tuple[Path, ...] = ()
    native_support_keys: tuple[str, ...] = ()
    required_headers: tuple[str, ...] = ()

    @property
    def source_files(self) -> tuple[Path, ...]:
        """Return all generated wrapper sources in compile order."""
        return (*self.bridge_sources, *self.binding_sources)

    @property
    def generated_files(self) -> tuple[Path, ...]:
        """Return all generated wrapper files, including headers."""
        return (*self.source_files, *self.header_files)


@dataclass
class RenderedGeneratedWrapperArtifacts(StageRecord):
    """Rendered generated sources plus compile/link metadata."""

    artifacts: GeneratedWrapperArtifacts
    sources: tuple[GeneratedSourceFile, ...]
    extension_init_name: str

    @property
    def source_paths(self) -> tuple[Path, ...]:
        """Return rendered source payload paths in write order."""
        return tuple(source.path for source in self.sources)
