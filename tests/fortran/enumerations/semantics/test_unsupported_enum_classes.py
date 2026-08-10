"""Tests split by stable ownership concept from `test_python_ast_contracts.py`."""

import pytest
from tests.fortran._support.pyi_conversion import parse_pyi_text


def test_convert_pyi_to_ir_rejects_enum_classes():
    source = """class status(Enum[Int]):
    pass
"""

    with pytest.raises(ValueError, match=r"Enum declarations are not supported"):
        parse_pyi_text(source, module_name="status_api")
