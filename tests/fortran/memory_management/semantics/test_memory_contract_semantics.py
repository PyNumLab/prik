"""Semantic ownership constraints for live views and immutable values."""

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text


def test_convert_pyi_to_ir_rejects_immutable_writable_borrowed_view_argument():
    with pytest.raises(ValueError, match="Immutable values cannot request"):
        parse_pyi_text(
            """
def normalize(
    values: Annotated[Float64[:], Immutable, Transfer("borrowed_view")]
) -> None: ...
""",
            module_name="invalid_immutable_view",
        )
