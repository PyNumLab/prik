"""Printer and loader agreement: generated and canonical contracts round-trip through semantic IR."""

import pytest
from hypothesis import (
    given,
    strategies as st,
)
from prik.policy.contract_imports import complete_contract_imports
from prik.policy.exports import complete_python_export_policy
from prik.printers import emit_module
from prik.pipeline.pyi import pyi_text_to_semantic_module as parse_pyi_text
from prik.semantics.models import (
    EXTERNAL_TYPE_REF_METADATA,
    ProjectionMapping,
    SemanticArgument,
    SemanticFunction,
    SemanticModule,
    SemanticType,
)
from tests.fortran._support.pyi_conversion import parse_pyi_text as parse_pyi_contract
from tests.fortran._support.semantic_properties import (
    _NATIVE_NAMES,
    _PYI_IDENTIFIER_STEMS,
    canonical_semantic_types,
)


@pytest.mark.property
@given(_NATIVE_NAMES)
def test_generated_pyi_escaping_round_trips_native_names(native_name):
    module = SemanticModule(
        name="generated",
        variables=[SemanticArgument(native_name, SemanticType("Int32", dtype="Int32"))],
        functions=[
            SemanticFunction(
                name="consume",
                native_name="consume",
                arguments=[SemanticArgument(native_name, SemanticType("Int32", dtype="Int32"))],
            )
        ],
    )

    emitted = emit_module(module)
    reparsed = parse_pyi_text(emitted, module_name="generated")

    assert reparsed.variables[0].name == native_name
    assert reparsed.functions[0].arguments[0].name == native_name


@pytest.mark.property
@given(st.lists(_PYI_IDENTIFIER_STEMS, min_size=1, max_size=6, unique=True))
def test_generated_pyi_synthetic_imports_are_stably_sorted(type_stems):
    type_names = [f"type_{stem}" for stem in type_stems]

    def import_lines(names):
        module = SemanticModule(
            name="generated",
            variables=[
                SemanticArgument(
                    f"value_{index}",
                    SemanticType(
                        type_name,
                        dtype=type_name,
                        metadata={
                            EXTERNAL_TYPE_REF_METADATA: {
                                "name": type_name,
                                "local_name": type_name,
                                "origin_module": "types",
                                "representation": "opaque",
                            }
                        },
                    ),
                )
                for index, type_name in enumerate(names)
            ],
        )
        complete_python_export_policy(module)
        complete_contract_imports([module])
        return [line for line in emit_module(module).splitlines() if line.startswith("from ")]

    expected = [f"from .types import {', '.join(sorted(type_names))}"]
    assert import_lines(type_names) == expected
    assert import_lines(reversed(type_names)) == expected


@pytest.mark.property
@given(st.lists(canonical_semantic_types(), max_size=5))
def test_generated_semantic_ir_round_trips_through_pyi(arguments):
    semantic_arguments = [
        SemanticArgument(f"value_{index}", semantic_type) for index, semantic_type in enumerate(arguments)
    ]
    module = SemanticModule(
        name="generated",
        functions=[
            SemanticFunction(
                name="consume",
                native_name="consume",
                arguments=semantic_arguments,
                projection=[
                    ProjectionMapping(
                        python_name=argument.name,
                        native_name=argument.name,
                        native_position=index,
                        python_position=index,
                    )
                    for index, argument in enumerate(semantic_arguments)
                ],
            )
        ],
    )

    emitted = emit_module(module)
    reparsed = parse_pyi_text(emitted, module_name="generated")

    assert emit_module(reparsed) == emitted
    assert parse_pyi_text(emit_module(reparsed), module_name="generated") == reparsed


CONTRACT_SPELLINGS = {
    "pointer-depths": """
deep: Addr[3](Float64)
shallow: Addr[2](Float64)
raw: Addr(Float64)
""",
    "array-descriptor-handles": """
grid: Allocatable[Float64[:, :]]
mask: Allocatable[Annotated[Bool[1], Finite]]
maybe: Annotated[Allocatable[Float64[:]], MaybeUnallocated]
target: Annotated[Pointer[Float64[:]], PointerAssociation("runtime")]
labels: Pointer[String[8][:]]
""",
    "array-layout-and-constraints": """
flat: Float64[Flat]
matrix: Float64[3, Flat]
c_matrix: Annotated[Float64[Flat, 3], ORDER_C]
c_dense: Annotated[Float64[:, :], ORDER_C]
any_order: Annotated[Float64[:, :], ORDER_ANY, Finite, Range(1, 3)]
bounded: Annotated[Int32, Bounded(1, 8), Finite]
""",
    "array-dimensions": """
def apply(
    A: Float64[LDA, N],
    work: Float64[::],
    bounded: Float64[0:n:],
    scratch: Float64[:],
    rank_any: Float64[...],
    computed: Float64[xl.size],
    scalar: Float64[()]
) -> None: ...
""",
    "copy-order": """
def consume(
    values: Annotated[Float64[:, :], ORDER_C, COPY_F]
) -> None: ...
""",
    "scalar-descriptors": """
scratch: Allocatable[Float64]
current: Pointer[Int32]
maybe_value: Float64 | None
label: String[16]
names: Allocatable[String[:]]

@native_call([Allocatable(Arg(0)), Pointer(Arg(1))], result=Pointer(Return(0)))
def combine(
    scale: Float64 | None,
    value: Int32 | None
) -> Float64 | None: ...
""",
    "optional-descriptor-handles": """
def maybe_consume(
    values: Allocatable[Float64[:]] | None = ...,
    target: Pointer[Float64[:]] | None = ...
) -> None: ...
""",
    "boolean-widths": """
def inspect(
    default: Bool,
    byte: Bool8[:],
    short: Bool16[:],
    word: Bool32[:],
    wide: Bool64[:]
) -> None: ...
""",
    "hidden-native-values": """
@native_call([Arg(0), Int32(1), Float64(0.5), Bool(False), String[1]("N"), Len(Arg(0)), Arg(0).shape[0], IsPresent(Arg(1)), Work('tmp')])
def wrapper(
    x: Float64[n],
    b: Int32 | None = ...
) -> None: ...
""",
    "return-and-work-references": """
@native_call([Len(Return(0)), Work('tmp').shape[1]])
def wrapper() -> Float64: ...
""",
    "typed-projections": """
@native_call([Int32(Arg(0).shape[0]), Int64(Arg(0).strides[0]), Arg(0), Int32(Len(Arg(1))), Arg(1), Arg(0).size, Int32(Arg(0).size), Int32(-1), Float64(-0.5), Complex64((1+2j))])
def scale(
    values: Float64[::],
    label: String[8]
) -> None: ...
""",
    "named-output-return": """
@native_call([Arg(0), Arg(1), Return('c', 0)])
def add(
    a: Float64,
    b: Float64
) -> Float64: ...
""",
    "value-transport-and-native-abi": """
@native_abi("c")
class point:
    x: Float64

@native_call([Value(Arg(0))])
def score(
    value: point
) -> Float64: ...

@native_abi("c")
@bind("renamed_entry")
@native_call([Addr(Arg(0)), Arg(0).shape[0], Return('result', 0)])
def transform(
    values: Float64[:]
) -> Float64: ...
""",
    "native-spellings-of-renamed-entities": """
@bind("native_state")
class state:
    tally: Annotated[Int32, SourceName("TALLY")]

counter: Annotated[Int32, SourceName("COUNTER")]
""",
    "plain-tuple-return": """
def pair(
    x: Int32
) -> tuple[Int32, Float64]: ...
""",
    "visibility-and-module-state": """
import iso_c_binding

class particle:
    id: Int32

scale: private[Float64]
answer: Final[Int32]
hidden_answer: private[Final[Int32]]
literal_answer: Final[Int32] = 42
output: Float64[:] = ...
var['class']: Int32

@private
@bind("native_helper")
def helper(
    value: private[Int32]
) -> None: ...
""",
}


@pytest.mark.parametrize("body", list(CONTRACT_SPELLINGS.values()), ids=list(CONTRACT_SPELLINGS))
def test_contract_spellings_round_trip_through_semantic_ir(body: str):
    """Each canonical spelling loads, prints back as written, and reloads to the same IR."""
    module = parse_pyi_contract(body, module_name="spellings")
    emitted = emit_module(module)

    emitted_lines = set(emitted.splitlines())
    assert [line for line in body.strip().splitlines() if line and line not in emitted_lines] == []
    assert parse_pyi_contract(emitted, module_name="spellings") == module
