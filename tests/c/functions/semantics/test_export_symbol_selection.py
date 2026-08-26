"""Semantic-IR ownership for exact C function export selection."""

from pathlib import Path

import pytest

from prik.cli import _read_c_export_symbols
from prik.parsers.c.models import CFile, CFunction, CInt, CVariable
from prik.semantics.c2ir import CToIRConverter, select_c_export_functions
from prik.semantics.metadata import EXPLICIT_C_EXPORT_METADATA


def _module_with_declarations():
    parsed = CFile(
        filename="probe.h",
        functions=[
            CFunction(name="keep", result_type=CInt()),
            CFunction(name="drop", result_type=CInt()),
        ],
        variables=[CVariable(name="state", type=CInt())],
    )
    return CToIRConverter().visit(parsed)


def test_export_selection_promotes_only_the_named_function():
    module = _module_with_declarations()
    module.functions[0].visibility = "private"

    selected = select_c_export_functions([module], ["keep"])

    assert selected == [module]
    assert [function.name for function in module.functions] == ["keep"]
    assert module.functions[0].visibility == "public"
    assert module.functions[0].metadata[EXPLICIT_C_EXPORT_METADATA] is True
    assert module.variables == []
    assert module.classes == []
    assert module.prototypes == []
    assert module.overload_sets == []


@pytest.mark.parametrize(
    ("symbols", "message"),
    [
        ([], "requires at least one function name"),
        (["bad-name"], "invalid C identifiers: bad-name"),
        (["keep", "keep"], "repeated names: keep"),
        (["missing"], "unknown names: missing"),
        (["state"], "non-function names: state"),
    ],
)
def test_export_selection_fails_closed_for_invalid_requests(symbols, message):
    with pytest.raises(ValueError, match=message):
        select_c_export_functions([_module_with_declarations()], symbols)


def test_export_selection_rejects_an_ambiguous_function_name():
    first = _module_with_declarations()
    second = _module_with_declarations()

    with pytest.raises(ValueError, match="ambiguous function names: keep"):
        select_c_export_functions([first, second], ["keep"])


def test_export_symbol_file_accepts_comments_and_rejects_duplicates(tmp_path: Path):
    export_file = tmp_path / "exports.txt"
    export_file.write_text("# reviewed\nkeep  # public\n\ndrop\n", encoding="utf-8")
    assert _read_c_export_symbols(export_file) == ("keep", "drop")

    export_file.write_text("keep\nkeep\n", encoding="utf-8")
    with pytest.raises(ValueError, match="first appeared on line 1"):
        _read_c_export_symbols(export_file)
