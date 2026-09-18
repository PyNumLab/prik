"""A reloaded contract publishes what its `__all__` states, and nothing else.

A generated contract writes a private prototype and a private generic into its
body, because annotations and dispatch resolve against them, while leaving both
out of `__all__`. Reading that contract back must not turn either into a public
declaration merely because it is still written there.
"""

from pathlib import Path

import pytest

from prik.pipeline.pyi import pyi_paths_to_semantic_modules
from prik.policy.exports import complete_python_export_policy
from prik.printers.pyi import PyiPrinter
from prik.semantics.models import PYTHON_EXPORTS_METADATA, ProcedureOverloadSet
from prik.semantics.fortran2ir import fortran_file_to_semantic_modules
from prik.parsers.fortran import parse_fortran_file

SOURCE = """\
module v_mod
  implicit none
  private

  abstract interface
    subroutine cb()
    end subroutine
  end interface

  interface hidden_generic
    module procedure hidden_one
  end interface

  public :: run
contains
  subroutine run(f)
    procedure(cb) :: f
    call f()
  end subroutine run

  subroutine hidden_one(a)
    integer, intent(in) :: a
    print *, a
  end subroutine hidden_one
end module v_mod
"""


@pytest.fixture
def generated_contract(tmp_path: Path) -> Path:
    """Write the source-derived contract for the shared module."""
    source = tmp_path / "v.f90"
    source.write_text(SOURCE, encoding="utf-8")
    module = fortran_file_to_semantic_modules(parse_fortran_file(SOURCE, filename=str(source)))[0]
    contract = tmp_path / "v_mod.pyi"
    contract.write_text(PyiPrinter().emit(module), encoding="utf-8")
    return contract


def test_a_contract_states_the_surface_without_publishing_its_helpers(generated_contract: Path):
    """The prototype and the generic are written but not exported."""
    text = generated_contract.read_text(encoding="utf-8")

    assert "def cb() -> None: ..." in text
    assert "def hidden_generic(" in text
    assert '__all__ = ["run"]' in text


def test_reloading_a_contract_does_not_publish_what_all_leaves_out(generated_contract: Path):
    """`__all__` is the stated surface, so no export is completed outside it.

    A prototype and a generic read back public by default, and the declarations
    stay written because annotations and imports resolve against them. Completed
    export policy is what decides publication, and it names only the surface the
    contract stated.
    """
    reloaded = pyi_paths_to_semantic_modules([generated_contract])[0]
    complete_python_export_policy(reloaded)

    assert reloaded.exported_names == ["run"]
    assert [item.name for item in reloaded.prototypes] == ["cb"]
    assert [item.name for item in reloaded.overload_sets] == ["hidden_generic"]

    published = {
        str(owner.name): (owner.procedures[0] if isinstance(owner, ProcedureOverloadSet) else owner).metadata.get(
            PYTHON_EXPORTS_METADATA
        )
        for owner in (*reloaded.functions, *reloaded.overload_sets)
    }
    assert published["run"] == [{"namespace": (), "name": "run"}]
    assert published["hidden_generic"] is None
    assert published["hidden_one"] is None


def test_a_contract_read_back_and_written_again_states_the_same_surface(generated_contract: Path):
    """Publication survives the round trip rather than drifting with each pass."""
    original = generated_contract.read_text(encoding="utf-8")
    reloaded = pyi_paths_to_semantic_modules([generated_contract])[0]

    assert PyiPrinter().emit(reloaded).strip() == original.strip()


def test_a_withheld_declaration_is_still_reachable_for_naming(generated_contract: Path):
    """Leaving a name out of `__all__` withholds publication, not reachability.

    Another module's annotation may still name the prototype, so the spelling
    this contract writes it under stays readable; what `__all__` decides is
    whether the module publishes it, which completed export policy settles.
    """
    reloaded = pyi_paths_to_semantic_modules([generated_contract])[0]

    assert PyiPrinter().published_names(reloaded)["cb"] == "cb"
