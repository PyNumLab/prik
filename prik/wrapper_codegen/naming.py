"""Stable backend symbols whose spelling stays within native compiler limits."""

from __future__ import annotations

import re
import zlib


class NativeSymbolNames:
    """Create stable backend symbols within native compiler limits."""

    @staticmethod
    def compact(owner_path: str, preferred: str, *, limit: int = 27) -> str:
        """Return a readable, collision-resistant symbol fragment."""
        readable = re.sub(r"\W", "_", preferred).casefold().strip("_") or "value"
        digest = f"{zlib.crc32(owner_path.encode('utf-8')):08x}"
        prefix_length = max(1, limit - len(digest) - 1)
        return f"{readable[:prefix_length]}_{digest}"
