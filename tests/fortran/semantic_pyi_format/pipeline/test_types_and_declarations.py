"""Tests split by stable ownership concept from `test_imports_and_packages.py`."""

from tests.fortran._support.printer_models import (
    ProjectionMapping,
    PyiPrinter,
    SemanticArgument,
    SemanticArrayContract,
    SemanticClass,
    SemanticConstraint,
    SemanticFunction,
    SemanticMethod,
    SemanticModule,
    SemanticOrigin,
    SemanticStorageContract,
    SemanticType,
    emit_module,
    fortran_module_to_semantic_module,
    generate_pyi,
    parse_fortran_source,
    parse_pyi_text,
    pytest,
)


def test_emit_basic_scalar_function():
    source = """
module math_mod

contains

subroutine add(a, b, c)

    real(8), intent(in) :: a
    real(8), intent(in) :: b
    real(8), intent(out) :: c

end subroutine

end module
"""

    code = generate_pyi(source)

    assert "def add(" in code

    assert "@native_call([Addr(Arg(0)), Addr(Arg(1)), Return('c', 0)])" in code
    assert "a: Float64" in code
    assert "b: Float64" in code
    assert "c: Addr(Float64)" not in code
    assert 'Returns["c"' not in code
    assert ") -> Float64: ..." in code


def test_fortran_generated_contracts_emit_python_name_and_bind_original_name():
    module = SemanticModule(
        name="math_mod",
        functions=[
            SemanticFunction(
                "SQUARE_R4",
                native_name="SQUARE_R4",
                arguments=[SemanticArgument("X", SemanticType("Float32"))],
                return_type=SemanticType("Float32"),
                origin=SemanticOrigin(source_language="fortran", native_name="SQUARE_R4", native_scope="math_mod"),
            )
        ],
        origin=SemanticOrigin(source_language="fortran", source_kind="module"),
    )

    code = emit_module(module, normalize_fortran_public_names=True)

    assert '@bind("SQUARE_R4")\ndef square_r4(' in code


def test_emit_rejects_unknown_semantic_type():
    module = SemanticModule(
        name="bad",
        variables=[
            SemanticArgument(
                name="x",
                semantic_type=SemanticType("Unknown", dtype="Unknown"),
            )
        ],
    )

    with pytest.raises(ValueError, match="unresolved semantic type 'Unknown'"):
        emit_module(module)


def test_emit_no_argument_subroutine_is_single_line_signature():
    source = """
module no_arg_mod

contains

subroutine ping()
end subroutine

end module
"""

    code = generate_pyi(source)

    assert "def ping() -> None: ..." in code
    assert "def ping(\n    \n)" not in code


def test_emit_array_constraints():
    source = """
module array_mod

contains

subroutine scale(x)

    real(8), intent(inout) :: x(:)

end subroutine

end module
"""

    code = generate_pyi(source)

    assert "def scale(" in code

    assert "Float64[" in code

    assert "Shape" not in code
    assert "Float64[::]" in code
    assert "ArrayCategory" not in code


def test_emit_matrix_shapes():
    source = """
module matrix_mod

contains

subroutine matvec(A, x, y)

    real(8), intent(in) :: A(:, :)
    real(8), intent(in) :: x(:)
    real(8), intent(out) :: y(:)

end subroutine

end module
"""

    code = generate_pyi(source)

    assert "A: Float64[::, ::]" in code
    assert "Shape" not in code
    assert "x: Float64[::]" in code
    assert "y: Float64[::]" in code
    assert "Annotated[Float64[::]" not in code
    assert "y: Float64[::]\n) -> None: ..." in code


def test_emit_explicit_bound_ranges_as_extents_without_source_dimension_metadata():
    source = """
module bound_mod
contains
subroutine bounded(n, default_bound, zero_bound, shifted_bound)
  integer, intent(in) :: n
  real(8), intent(inout) :: default_bound(1:n)
  real(8), intent(inout) :: zero_bound(0:n-1)
  real(8), intent(inout) :: shifted_bound(2:n+1)
end subroutine bounded
end module bound_mod
"""
    code = generate_pyi(source)

    assert "default_bound: Float64[n]" in code
    assert "zero_bound: Float64[n]" in code
    assert "shifted_bound: Float64[n]" in code
    assert "ArrayCategory" not in code


def test_emit_optional_argument():
    source = """
module opt_mod

contains

subroutine solve(A, tol)

    real(8), intent(in) :: A(:, :)
    real(8), intent(in), optional :: tol

end subroutine

end module
"""

    code = generate_pyi(source)

    assert "tol:" in code

    assert "= ..." in code


def test_emit_function_result():
    source = """
module func_mod

contains

function norm2(x) result(r)

    real(8), intent(in) :: x(:)

    real(8) :: r

end function

end module
"""

    code = generate_pyi(source)

    assert "def norm2(" in code

    assert "-> Float64" in code


def test_emit_explicit_shape():
    source = """
module shape_mod

contains

subroutine foo(A)

    real(8), intent(in) :: A(10, 20)

end subroutine

end module
"""

    code = generate_pyi(source)

    assert "A: Float64[10, 20]" in code


def test_parameter_target_sanitizes_non_identifier_names():
    assert PyiPrinter._parameter_target("has-dash") == "has_dash"
    assert PyiPrinter._parameter_target("1value") == "arg_1value"
    assert PyiPrinter._parameter_target("class!") == "class_"
    assert PyiPrinter._parameter_target("!!!") == "arg"
    assert PyiPrinter._requires_explicit_projection_mapping(ProjectionMapping(native_position=1, result_position=0))


def test_emit_argument_escapes_original_name_metadata():
    emitted = PyiPrinter().emit(SemanticArgument('quote"name', SemanticType("Int32")))
    reparsed = parse_pyi_text(f"def consume({emitted}) -> None: ...\n", module_name="quoted")

    assert emitted == 'quote_name: Annotated[Int32, SourceName("quote\\"name")]'
    assert reparsed.functions[0].arguments[0].name == 'quote"name'


def test_emit_multiple_functions():
    source = """
module multi_mod

contains

subroutine foo(x)

    integer, intent(in) :: x

end subroutine

subroutine bar(y)

    real(8), intent(in) :: y

end subroutine

end module
"""

    code = generate_pyi(source)

    assert "def foo(" in code

    assert "def bar(" in code


def test_emit_complex_fem_module():
    source = """
module fem_mod

type :: mesh

    integer :: nelements
    integer :: nnodes

end type

contains

subroutine assemble(K, coords, connectivity)

    real(8), intent(out) :: K(:, :)

    real(8), intent(in) :: coords(:, :)

    integer, intent(in) :: connectivity(:, :)

end subroutine

function compute_norm(x) result(r)

    real(8), intent(in) :: x(:)

    real(8) :: r

end function

end module
"""

    code = generate_pyi(source)

    # --------------------------------------------------------
    # Class
    # --------------------------------------------------------

    assert "class mesh" in code

    # --------------------------------------------------------
    # Procedures
    # --------------------------------------------------------

    assert "def assemble(" in code

    assert "def compute_norm(" in code

    # --------------------------------------------------------
    # Matrix annotations
    # --------------------------------------------------------

    assert "K: Float64[::, ::]" in code
    assert "connectivity: Int32[::, ::]\n) -> None: ..." in code

    assert "coords: Float64[::, ::]" in code

    assert "connectivity: Int32[::, ::]" in code

    # --------------------------------------------------------
    # Return type
    # --------------------------------------------------------

    assert "def compute_norm(" in code
    assert ") -> Float64: ..." in code


def test_emit_empty_module():
    source = """
module empty_mod
end module
"""

    code = generate_pyi(source)

    assert isinstance(code, str)


def test_emit_is_deterministic():
    source = """
module stable_mod

contains

subroutine foo(x)

    integer, intent(in) :: x

end subroutine

end module
"""

    code1 = generate_pyi(source)

    code2 = generate_pyi(source)

    assert code1 == code2


def test_printer_emit_visitor_dispatches_semantic_models():
    printer = PyiPrinter()
    constraint = SemanticConstraint("Finite")
    semantic_type = SemanticType(
        "Float64",
        dtype="Float64",
        rank=1,
        shape=[":"],
        storage=SemanticStorageContract(
            kind="array",
            array=SemanticArrayContract(rank=1, shape=[":"], source_shape=[":"]),
        ),
    )
    argument = SemanticArgument("class", semantic_type, optional=True)
    method = SemanticMethod(name="reset")
    cls = SemanticClass(
        name="thing",
        fields=[SemanticArgument("bad-name", semantic_type)],
        methods=[method],
        visibility="private",
    )
    func = SemanticFunction(name="wrap", arguments=[argument])
    module = SemanticModule(name="visitor_mod", classes=[cls], functions=[func])

    assert printer.emit(constraint) == "Finite"
    assert printer.emit(semantic_type) == "Float64[:]"
    assert printer.emit(argument) == 'class_: Annotated[Float64[:], SourceName("class")] = ...'
    assert "def reset(self) -> None: ..." in printer.emit(method)
    assert "@private\nclass thing:" in printer.emit(cls)
    assert "var['bad-name']: Float64[:]" in printer.emit(cls)
    assert "def wrap(" in printer.emit(func)
    assert "class thing:" in printer.emit(module)

    with pytest.raises(TypeError) as unsupported:
        printer.emit(object())
    assert str(unsupported.value) == "Unsupported semantic model for .pyi emission: <class 'object'>"


def test_printer_emits_flat_dimension_for_assumed_size_arrays():
    fortran_type = SemanticType(
        "Float64",
        dtype="Float64",
        rank=2,
        shape=["3", ":"],
        storage=SemanticStorageContract(
            kind="array",
            array=SemanticArrayContract(
                rank=2,
                shape=["3", ":"],
                category="assumed_size",
                source_shape=["3", "*"],
                order="ORDER_F",
                contiguous=True,
            ),
        ),
    )
    c_type = SemanticType(
        "Float64",
        dtype="Float64",
        rank=2,
        shape=[":", "3"],
        storage=SemanticStorageContract(
            kind="array",
            array=SemanticArrayContract(
                rank=2,
                shape=[":", "3"],
                category="assumed_size",
                source_shape=["*", "3"],
                order="ORDER_C",
                contiguous=True,
            ),
        ),
    )

    assert PyiPrinter().emit(fortran_type) == "Float64[3, Flat]"
    assert PyiPrinter().emit(c_type) == "Annotated[Float64[Flat, 3], ORDER_C]"

    nondefault_c_type = SemanticType(
        "Float64",
        dtype="Float64",
        rank=2,
        shape=[":", ":"],
        storage=SemanticStorageContract(
            kind="array",
            array=SemanticArrayContract(
                rank=2,
                shape=[":", ":"],
                source_shape=[":", ":"],
                order="ORDER_C",
                contiguous=True,
            ),
        ),
    )
    assert PyiPrinter().emit(nondefault_c_type) == "Annotated[Float64[:, :], ORDER_C]"

    lower_bound_assumed_size = SemanticType(
        "Float64",
        dtype="Float64",
        rank=1,
        shape=[":"],
        storage=SemanticStorageContract(
            kind="array",
            array=SemanticArrayContract(
                rank=1,
                shape=[":"],
                category="assumed_size",
                source_shape=["0:*"],
                order="ORDER_F",
                contiguous=True,
            ),
        ),
    )
    assert PyiPrinter().emit(lower_bound_assumed_size) == "Float64[Flat]"

    bounded_assumed_size = SemanticType(
        "Float64",
        dtype="Float64",
        rank=2,
        shape=["LDB", ":"],
        storage=SemanticStorageContract(
            kind="array",
            array=SemanticArrayContract(
                rank=2,
                shape=["LDB", ":"],
                category="assumed_size",
                source_shape=["0:LDB-1", "0:*"],
                order="ORDER_F",
                contiguous=True,
            ),
        ),
    )
    assert PyiPrinter().emit(bounded_assumed_size) == "Float64[LDB, Flat]"


def test_emit_fortran_parameter_defaults_only_when_resolved_to_literals():
    source = """
module trig_constants
  real, parameter :: c = cos(0.0)
  integer, parameter :: n = 3 + 4
end module
"""
    code = generate_pyi(source)

    assert "c: Final[Float32]\n" in code
    assert "c: Final[Float32] = cos(0.0)" not in code
    assert "n: Final[Int32] = 7" in code


def test_fortran_derived_value_dummy_emits_value_native_projection():
    source = """
module value_contract
  type :: item
    real(8) :: x
  end type item
contains
  function score(value) result(total)
    type(item), value :: value
    real(8) :: total
    total = value%x
  end function score
end module value_contract
"""

    code = generate_pyi(source)

    assert "@native_call([Value(Arg(0))])" in code
    assert "value: item" in code


def test_character_array_pyi_spelling_round_trips_fixed_and_deferred_lengths():
    source = """
module char_array_mod
contains
  subroutine use_labels(labels)
    character(len=4), intent(in) :: labels(:)
  end subroutine use_labels
  subroutine replace_names(names)
    character(len=:), allocatable, intent(inout) :: names(:)
  end subroutine replace_names
end module char_array_mod
"""
    semantic_module = fortran_module_to_semantic_module(parse_fortran_source(source))
    emitted = emit_module(semantic_module)

    assert "String[4][::]" in emitted
    assert "Allocatable[String[:][:]]" in emitted

    parsed = parse_pyi_text(emitted, module_name="char_array_mod")
    use_labels = next(func for func in parsed.functions if func.name == "use_labels")
    assert use_labels.arguments[0].semantic_type.metadata["fortran_character_length"] == "4"

    replace_names = next(func for func in parsed.functions if func.name == "replace_names")
    names_type = replace_names.arguments[0].semantic_type
    assert names_type.metadata["fortran_character_length"] == ":"
    assert names_type.storage.array.allocatable is True
