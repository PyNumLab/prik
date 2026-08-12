"""Stable backend symbols shared by planning and native code generation."""

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


if __name__ == "__main__":
    owner = "geometry.point.coordinates"
    symbol = NativeSymbolNames.compact(owner, "point_coordinate_descriptor")

    print(f"Owner identity: {owner}")
    print(f"Stable native symbol: {symbol}")
    print(f"Within 27-character limit: {len(symbol) <= 27}")
