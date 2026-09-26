"""Allocatable descriptor lowering from completed wrapper policy."""

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.completion import complete_semantic_policies
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner


def _c_source(contract: str, module_name: str) -> str:
    module = parse_pyi_text(contract, module_name=module_name)
    complete_semantic_policies(module)
    artifacts = WrapperGenerator().generate(WrapperPlanner().build(module))
    return next(source.text for source in artifacts.sources if source.path.suffix == ".c")


ALLOCATABLE_ARGUMENT_CONTRACT = """
from prik.contracts import Allocatable, Float64, native_call, nogil

@nogil
@native_call([])
def total(values: Allocatable[Float64[:]]) -> Float64: ...

plain_allocatable: Allocatable[Float64[:]]
"""

FIXED_CHARACTER_OWNER_CONTRACT = """
from prik.contracts import Allocatable, Returns, String, nogil

@nogil
def rewrite(
    values: Allocatable[String[4][:]],
) -> Returns["values", Allocatable[String[4][:]]]: ...
"""


def test_maybe_unallocated_is_only_valid_on_direct_allocatable_array_results():
    module = parse_pyi_text(
        """
from prik.contracts import Allocatable, Annotated, Float64, MaybeUnallocated

def invalid_argument(values: Annotated[Allocatable[Float64[:]], MaybeUnallocated]) -> Float64: ...
""",
        module_name="invalid_maybe_unallocated",
    )

    with pytest.raises(ValueError, match="MaybeUnallocated metadata"):
        complete_semantic_policies(module)


def test_no_generated_binding_establishes_an_allocated_allocatable_descriptor():
    """CFI_establish reserves the allocatable descriptor for the Fortran runtime.

    F2018 18.5.5.6 requires a null ``base_addr`` when the attribute is
    ``CFI_attribute_allocatable``: an allocatable established from C must start
    unallocated.  Pairing that attribute with a real address describes an
    already-allocated allocatable, which ifx rejects with
    ``CFI_ERROR_BASE_ADDR_NOT_NULL`` while gfortran silently accepts it, so the
    gfortran end-to-end suite cannot catch it.
    """
    c_source = _c_source(ALLOCATABLE_ARGUMENT_CONTRACT, "allocatable_actuals")

    forged = [
        line.strip()
        for line in c_source.splitlines()
        if "CFI_establish(" in line and "CFI_attribute_allocatable" in line and ", NULL," not in line
    ]
    assert forged == []


@pytest.mark.parametrize(
    ("contract", "wrapper", "native_call", "lease"),
    [
        pytest.param(
            ALLOCATABLE_ARGUMENT_CONTRACT,
            "static void wrap_total_call_with_carrier_0(",
            "bind_c_total(",
            False,
            id="descriptor-consumer",
        ),
        pytest.param(
            FIXED_CHARACTER_OWNER_CONTRACT,
            "static PyObject * wrap_rewrite",
            "bind_c_rewrite(",
            True,
            id="leased-fortran-owner",
        ),
    ],
)
def test_nogil_releases_only_around_the_native_call(contract: str, wrapper: str, native_call: str, lease: bool):
    """The GIL is released only while Fortran runs, inside any owner lease."""
    c_source = _c_source(contract, "nogil_allocatables")
    start = c_source.index(wrapper)
    body = c_source[start:]

    begin = body.index("Py_BEGIN_ALLOW_THREADS")
    call = body.index(native_call)
    finish = body.index("Py_END_ALLOW_THREADS")
    assert begin < call < finish
    if lease:
        assert body.index("prik_native_array_backend_acquire_call") < begin
        assert finish < body.index("prik_native_array_backend_release_call")
