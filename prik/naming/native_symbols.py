"""Stable backend symbols shared by planning and native code generation."""

from __future__ import annotations

import re
import zlib


COLLISION_ADAPTER_PREFIX = "prik_collision_adapter_"
# Every compiler PRIK profiles accepts the GNU visibility attribute.
COLLISION_ADAPTER_STORAGE = '__attribute__((visibility("hidden")))'


class NativeSymbolNames:
    """Create stable backend symbols within native compiler limits."""

    @staticmethod
    def compact(owner_path: str, preferred: str, *, limit: int = 27) -> str:
        """Return a readable, collision-resistant symbol fragment."""
        readable = re.sub(r"\W", "_", preferred).casefold().strip("_") or "value"
        digest = f"{zlib.crc32(owner_path.encode('utf-8')):08x}"
        prefix_length = max(1, limit - len(digest) - 1)
        return f"{readable[:prefix_length]}_{digest}"

    @staticmethod
    def collision_adapter(symbol_name: str) -> str:
        """Return the forwarder symbol that stands in for one native symbol.

        The binding calls this name instead of ``symbol_name`` so its own
        declaration cannot collide with a declaration of the same identifier
        that ``Python.h`` already brought into the binding translation unit.
        """
        return f"{COLLISION_ADAPTER_PREFIX}{symbol_name}"


if __name__ == "__main__":
    owner = "geometry.point.coordinates"
    symbol = NativeSymbolNames.compact(owner, "point_coordinate_descriptor")

    print(f"Owner identity: {owner}")
    print(f"Stable native symbol: {symbol}")
    print(f"Within 27-character limit: {len(symbol) <= 27}")
