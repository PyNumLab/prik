"""Tests split by stable ownership concept from `test_python_ast_contracts.py`."""

from tests.fortran._support.pyi_conversion import parse_pyi_text, pytest


def test_convert_pyi_to_ir_resolves_prik_overload_by_explicit_specific_name():
    module = parse_pyi_text(
        """
@bind("convert_integer_native")
def convert_integer(value: Int32) -> Int32: ...

@overload("convert_integer")
def convert(value: Int32) -> Int32: ...
""",
        module_name="generic_mod",
    )

    assert [function.name for function in module.functions] == ["convert_integer"]
    assert [(item.name, [procedure.name for procedure in item.procedures]) for item in module.overload_sets] == [
        ("convert", ["convert_integer"])
    ]
    assert module.overload_sets[0].procedures[0].metadata["overload_target"] == "convert_integer"
    assert module.overload_sets[0].procedures[0].native_name == "convert_integer_native"


@pytest.mark.parametrize(
    ("source", "message"),
    [
        (
            "@overload\ndef convert(value: Int32) -> Int32: ...\n",
            "overload expects one specific procedure name",
        ),
        (
            "from typing import overload\n",
            "typing.overload is not supported",
        ),
        (
            """
def convert_integer(value: Int32) -> Int32: ...

@overload("convert_integer", generic="convert")
def convert_number(value: Int32) -> Int32: ...
""",
            "generic is only valid for class overloads; use bind on a module overload",
        ),
        (
            """
def compare(left: item, right: item) -> Bool: ...
class item:
    @overload("compare", generic="operator(.eqv.)")
    def __add__(self, right: item) -> Bool: ...
""",
            "generic 'operator\\(\\.eqv\\.\\)' is incompatible with method '__add__'",
        ),
        (
            '@overload("missing")\ndef convert(value: Int32) -> Int32: ...\n',
            "missing specific procedure 'missing'",
        ),
        (
            """
def convert_integer(value: Int32) -> Int32: ...
def convert_integer(value: Int32) -> Int32: ...
@overload("convert_integer")
def convert(value: Int32) -> Int32: ...
""",
            "target 'convert_integer' is ambiguous",
        ),
        (
            """
def convert_integer(value: Int32) -> Int32: ...
@overload("convert_integer")
def convert(value: Float64) -> Int32: ...
""",
            "declaration 'convert' is incompatible",
        ),
        (
            """
def convert_integer(value: Int32) -> Int32: ...
@overload("convert_integer")
def convert(value: Int32) -> Int32: ...
@overload("convert_integer")
def convert(value: Int32) -> Int32: ...
""",
            "references specific procedure 'convert_integer' more than once",
        ),
        (
            """
def convert_integer(value: Int32) -> Int32: ...
@overload("convert_integer")
@native_call([Addr(Arg(0))])
def convert(value: Int32) -> Int32: ...
""",
            "overload cannot be combined with native_call",
        ),
        (
            """
def set_integer(self: item, value: Int32) -> None: ...
class item:
    @overload("set_integer")
    @native_call([Pass(), Addr(Arg(0))])
    def set(self, value: Int32) -> None: ...
""",
            "overload cannot be combined with native_call",
        ),
    ],
)
def test_convert_pyi_to_ir_rejects_invalid_prik_overload_links(source: str, message: str):
    with pytest.raises(ValueError, match=message):
        parse_pyi_text(source, module_name="generic_mod")
