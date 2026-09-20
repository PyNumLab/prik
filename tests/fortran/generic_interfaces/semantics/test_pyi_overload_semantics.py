"""Tests split by stable ownership concept from `test_python_ast_contracts.py`."""

import pytest
from tests.fortran._support.pyi_conversion import parse_pyi_text


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


def test_overload_accepts_a_specific_that_projects_an_output_array_to_its_result():
    """A projected array output matches a declared result that states no mutability.

    An `intent(out)` allocatable dummy is written through as an argument, and a
    projection returns it as an ordinary result. That write-through belongs to
    the argument passing, so a declared result type -- which states no such
    thing -- still names the same value.
    """
    module = parse_pyi_text(
        """
@native_call([Return('x', 0), Addr(Arg(0))])
def alloc_vector(n: Int32) -> Allocatable[Int32[:]]: ...

@bind("safealloc")
@overload("alloc_vector")
def safealloc(n: Int32) -> Allocatable[Int32[:]]: ...
""",
        module_name="memory_mod",
    )

    assert [(item.name, [procedure.name for procedure in item.procedures]) for item in module.overload_sets] == [
        ("safealloc", ["alloc_vector"])
    ]


@pytest.mark.parametrize(
    "declared_result",
    ["Allocatable[Float64[:]]", "Allocatable[Int32[:, :]]", "Int32"],
)
def test_overload_still_rejects_a_projected_result_of_another_type(declared_result: str):
    """Neutralizing write-through leaves every other result difference compared."""
    source = f"""
@native_call([Return('x', 0), Addr(Arg(0))])
def alloc_vector(n: Int32) -> Allocatable[Int32[:]]: ...

@bind("safealloc")
@overload("alloc_vector")
def safealloc(n: Int32) -> {declared_result}: ...
"""

    with pytest.raises(ValueError, match="declaration 'safealloc' is incompatible"):
        parse_pyi_text(source, module_name="memory_mod")


def test_overload_accepts_a_specific_that_projects_a_scalar_descriptor_to_its_result():
    """A nullable descriptor result is the only form an overload can restate.

    A native scalar descriptor result is written as a nullable value plus a
    `native_call` result wrapper, and an overload declaration may carry no
    `native_call`. The declaration therefore spells the visible value alone, as
    the contract printer emits it.
    """
    module = parse_pyi_text(
        """
@native_call([Allocatable(Return('x', 0)), Addr(Arg(0))])
def alloc_character(n: Int32) -> String[:] | None: ...

@bind("safealloc")
@overload("alloc_character")
def safealloc(n: Int32) -> String[:] | None: ...
""",
        module_name="memory_mod",
    )

    assert [(item.name, [procedure.name for procedure in item.procedures]) for item in module.overload_sets] == [
        ("safealloc", ["alloc_character"])
    ]


@pytest.mark.parametrize("declared_result", ["String", "Int32[:] | None", "Float64[:] | None"])
def test_overload_still_rejects_a_projected_descriptor_of_another_type(declared_result: str):
    """Reading a descriptor result as nullable leaves every other difference compared."""
    source = f"""
@native_call([Allocatable(Return('x', 0)), Addr(Arg(0))])
def alloc_character(n: Int32) -> String[:] | None: ...

@bind("safealloc")
@overload("alloc_character")
def safealloc(n: Int32) -> {declared_result}: ...
"""

    with pytest.raises(ValueError, match="declaration 'safealloc' is incompatible"):
        parse_pyi_text(source, module_name="memory_mod")
