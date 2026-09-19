"""A re-exported module variable is another route to one native variable.

Publishing a variable in a second namespace adds Python names only. The native
storage, accessors, allocation state, and pointer association stay single, so
every publication observes the same changes whichever one made them.
"""

from pathlib import Path

import numpy as np
import pytest

from prik.pipeline.build import build_fortran_extension, build_pyi_extension
from tests.fortran._support.wrapper_build import _generate_checked_pyi_contract, _import_from_build_dir

pytestmark = pytest.mark.fortran_end_to_end

SOURCE = """\
module store_mod
  implicit none
  integer :: counter = 5
  integer, parameter :: limit = 42
  character(len=8) :: label = 'first   '
  character(len=4) :: tags(2) = ['ab  ', 'cd  ']
  real(8), allocatable :: values(:)
  real(8), pointer :: view(:) => null()
  real(8), target :: backing(4) = [1.0d0, 2.0d0, 3.0d0, 4.0d0]
contains
  subroutine allocate_values(n)
    integer, intent(in) :: n
    if (allocated(values)) deallocate(values)
    allocate(values(n))
    values = 1.0d0
  end subroutine allocate_values

  subroutine release_values()
    if (allocated(values)) deallocate(values)
  end subroutine release_values

  subroutine associate_view()
    view => backing
  end subroutine associate_view

  subroutine clear_view()
    view => null()
  end subroutine clear_view

end module store_mod

module facade_mod
  use store_mod, only : counter, limit, label, tags, values, view
  implicit none
  public :: counter, limit, label, tags, values, view
end module facade_mod

module renamed_mod
  use store_mod, only : tally => counter
  implicit none
  public :: tally
end module renamed_mod

module hop_mod
  use renamed_mod, only : tally
  implicit none
  public :: tally
end module hop_mod
"""


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    """Build the shared source project once for the read-only checks."""
    tmp_path = tmp_path_factory.mktemp("variable_reexport")
    source = tmp_path / "store.f90"
    source.write_text(SOURCE, encoding="utf-8")
    result = build_fortran_extension(source, output_dir=tmp_path / "build", output_name="store_api")
    return _import_from_build_dir(result.module_name, result.output_dir)


def test_a_scalar_publication_reads_and_writes_one_native_variable(built):
    """Both namespaces name the same storage, so either one observes the other."""
    built.store_mod.counter = np.int32(11)
    assert built.facade_mod.counter == np.int32(11)

    built.facade_mod.counter = np.int32(23)
    assert built.store_mod.counter == np.int32(23)


def test_a_renamed_publication_reaches_the_same_variable(built):
    """A rename changes the Python name a namespace binds, never the variable."""
    built.store_mod.counter = np.int32(31)
    assert built.renamed_mod.tally == np.int32(31)

    built.renamed_mod.tally = np.int32(37)
    assert built.store_mod.counter == np.int32(37)


def test_a_multi_hop_publication_resolves_to_the_declaring_variable(built):
    """A -> B -> C publishes what A declares, not a copy B made."""
    built.store_mod.counter = np.int32(41)
    assert built.hop_mod.tally == np.int32(41)

    built.hop_mod.tally = np.int32(43)
    assert built.store_mod.counter == np.int32(43)
    assert built.renamed_mod.tally == np.int32(43)


def test_a_character_scalar_and_array_publish_one_storage(built):
    """String storage is shared the same way a scalar is."""
    built.store_mod.label = "second  "
    assert built.facade_mod.label == "second  "

    built.store_mod.tags[0] = b"zz  "
    assert bytes(built.facade_mod.tags[0]) == b"zz  "


def test_allocation_state_is_one_state_for_every_publication(built):
    """Allocating through the declaring module is visible through the facade."""
    built.store_mod.release_values()
    assert built.facade_mod.values.allocated is False

    built.store_mod.allocate_values(np.int32(3))
    assert built.facade_mod.values.allocated is True
    assert built.facade_mod.values.shape == (3,)

    # Reallocating to another extent replaces the one descriptor both see.
    built.store_mod.allocate_values(np.int32(5))
    assert built.facade_mod.values.shape == (5,)

    built.store_mod.release_values()
    assert built.facade_mod.values.allocated is False


def test_pointer_association_is_one_association_for_every_publication(built):
    """Associating and nullifying reach every namespace publishing the pointer."""
    built.store_mod.clear_view()
    assert built.facade_mod.view.associated is False

    built.store_mod.associate_view()
    assert built.facade_mod.view.associated is True
    assert built.facade_mod.view.shape == (4,)

    built.store_mod.clear_view()
    assert built.facade_mod.view.associated is False


def test_publishing_a_protected_variable_keeps_the_documented_refusal(tmp_path: Path):
    """A second namespace adds names, so it cannot make an unsupported form work.

    PRIK refuses `protected` because a generated accessor cannot define the
    variable outside its own module, and re-exporting it changes nothing about
    that.
    """
    source = tmp_path / "guarded.f90"
    source.write_text(
        """\
module guard_mod
  implicit none
  integer, protected :: guarded = 9
end module guard_mod

module guard_facade
  use guard_mod, only : guarded
  implicit none
  public :: guarded
end module guard_facade
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as error:
        build_fortran_extension(
            source,
            output_dir=tmp_path / "build",
            output_name="guard_api",
            generate_sources=True,
        )

    assert "is PROTECTED" in str(error.value)


def test_a_parameter_publishes_a_value_rather_than_shared_storage(built):
    """A `parameter` has no storage to share, so each namespace holds the value.

    Assignment is not refused, and rebinding one name changes neither the
    Fortran parameter nor any other namespace publishing it.
    """
    assert built.store_mod.limit == np.int32(42)
    assert built.facade_mod.limit == np.int32(42)

    built.facade_mod.limit = np.int32(7)

    assert built.facade_mod.limit == np.int32(7)
    assert built.store_mod.limit == np.int32(42)


def test_one_native_accessor_serves_every_publication(tmp_path: Path):
    """The second namespace adds names, so no second accessor is generated."""
    source = tmp_path / "store.f90"
    source.write_text(SOURCE, encoding="utf-8")

    result = build_fortran_extension(
        source,
        output_dir=tmp_path / "generated",
        output_name="accessor_api",
        generate_sources=True,
    )
    wrapper = (result.output_dir / "accessor_api_wrapper.c").read_text(encoding="utf-8")

    # One getter and one setter definition carry `counter`, however many
    # namespaces publish it; the four dispatches all call the same pair.
    assert wrapper.count("static PyObject * module_get_counter(void) {") == 1
    assert wrapper.count("static int module_set_counter(PyObject * value_obj) {") == 1
    assert wrapper.count("return module_get_counter();") == 4


def test_a_facade_may_publish_a_variable_its_declaring_namespace_hides(tmp_path: Path):
    """Owning the one variable plan must not put the declaring module in Python."""
    source = tmp_path / "store.f90"
    source.write_text(
        """\
module home_mod
  implicit none
  integer :: counter = 5
end module home_mod
""",
        encoding="utf-8",
    )
    package = tmp_path / "contracts"
    package.mkdir()
    (package / "home_mod.pyi").write_text(
        "from prik.contracts import Int32\n\ncounter: Int32\n\n__all__ = []\n",
        encoding="utf-8",
    )
    (package / "facade.pyi").write_text(
        'from .home_mod import counter\n\n__all__ = ["counter"]\n',
        encoding="utf-8",
    )
    (package / "__init__.pyi").write_text(
        'from . import facade\n\n__all__ = ["facade"]\n',
        encoding="utf-8",
    )

    result = build_pyi_extension(
        package / "__init__.pyi",
        native_fortran_sources=[str(source)],
        output_dir=tmp_path / "build",
        output_name="hidden_home_api",
    )
    module = result.import_module()

    assert module.facade.counter == np.int32(5)
    module.facade.counter = np.int32(17)
    assert module.facade.counter == np.int32(17)
    # The declaring module publishes nothing, so it is not a Python namespace.
    assert not hasattr(module, "home_mod")


def test_a_generated_contract_publishes_the_same_variables_as_its_source(tmp_path: Path):
    """Both routes reach one variable, so the two builds publish the same surface."""
    source = tmp_path / "store.f90"
    source.write_text(SOURCE, encoding="utf-8")

    source_result = build_fortran_extension(
        source,
        output_dir=tmp_path / "source_build",
        output_name="parity_source",
    )
    contracts = tmp_path / "contracts"
    _generate_checked_pyi_contract(source, contracts, None)
    contract_result = build_pyi_extension(
        contracts / "__init__.pyi",
        native_fortran_sources=[str(source)],
        output_dir=tmp_path / "contract_build",
        output_name="parity_contract",
    )

    from_source = _import_from_build_dir(source_result.module_name, source_result.output_dir)
    from_contract = _import_from_build_dir(contract_result.module_name, contract_result.output_dir)

    def surface(module):
        return {
            namespace: sorted(n for n in dir(getattr(module, namespace)) if not n.startswith("_"))
            for namespace in ("store_mod", "facade_mod", "renamed_mod", "hop_mod")
        }

    assert surface(from_source) == surface(from_contract)

    # The contract route reaches the same native variable, not a copy of it.
    from_contract.facade_mod.counter = np.int32(61)
    assert from_contract.store_mod.counter == np.int32(61)
    assert from_contract.hop_mod.tally == np.int32(61)
